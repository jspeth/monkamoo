import OpenAI from "openai";
import { getLogger } from "../logger.js";
import { getStorageWithFallback } from "../storage/factory.js";
import { registerClass } from "./classRegistry.js";
import { Player } from "./player.js";

const logger = getLogger("monkamoo.aiplayer");

export class AIPlayer extends Player {
  /** Represents an AI player in the MOO. */

  static typeName = "AIPlayer";

  constructor(props = {}) {
    super(props);

    // Initialize AI client with API key and configuration
    const apiKey = process.env.OPENAI_API_KEY;
    const baseURL = process.env.OPENAI_BASE_URL || undefined;
    this.useTools = (process.env.AI_USE_TOOLS || "true").toLowerCase() === "true";
    this.model = process.env.AI_MODEL || "o4-mini-2025-04-16";

    if (apiKey) {
      this.client = new OpenAI({ apiKey, baseURL });
      logger.info("aiplayer=%s: Created client with model %s", this.name, this.model);
    } else {
      this.client = null;
      logger.warning("aiplayer=%s: No API key configured, AI functionality disabled", this.name);
    }

    this.storage = null;
    this.history = null;
    // History loads asynchronously; handleMessage awaits this before using it.
    this.historyPromise = this.loadHistory().catch((error) => {
      logger.exception(error, "aiplayer=%s: failed to load history", this.name);
      this.history = this.defaultHistory();
    });
    this.capturedMessages = null;
    this.sleeping = false;
    this.debugging = false;
  }

  async getStorage() {
    if (!this.storage) {
      this.storage = await getStorageWithFallback();
    }
    return this.storage;
  }

  do_model(command) {
    if (command.indirectObjectStr) {
      this.model = command.indirectObjectStr;
      this.useTools = true;
    }
    this.room.announce(this, `${this.name} model is now ${this.model}.`, true);
  }

  debug(_command) {
    this.debugging = !this.debugging;
    this.room.announce(this, `${this.name} debugging is now ${this.debugging}.`, true);
  }

  sleep(_command) {
    this.sleeping = true;
    this.room.announce(this, `${this.name} goes to sleep.`, true);
  }

  wake(_command) {
    this.sleeping = false;
    this.room.announce(this, `${this.name} wakes up.`, true);
  }

  defaultHistory() {
    return [
      {
        role: "system",
        content: `Responses should be in the third person, like in a story, e.g. "${this.name} says..." or "${this.name} looks around the room...".`,
      },
    ];
  }

  async loadHistory() {
    const storage = await this.getStorage();
    const history = await storage.loadAIHistory(this.name);
    this.history = history ? this.migrateLegacyToolCalls(history) : this.defaultHistory();
  }

  // Bot histories saved before the tool-calling migration use the deprecated
  // assistant.function_call / role:"function" shape. Sending that alongside
  // a current `tools` request makes providers reject the whole call (422),
  // which is why old bots like Aurora appeared "offline". Upgrade in place.
  migrateLegacyToolCalls(history) {
    let migrated = false;
    let pendingToolCallId = null;
    const result = history.map((message, index) => {
      if (message.role === "assistant" && message.function_call) {
        migrated = true;
        pendingToolCallId = `legacy-${index}`;
        const { function_call, ...rest } = message;
        return { ...rest, tool_calls: [{ id: pendingToolCallId, type: "function", function: function_call }] };
      }
      if (message.role === "function" && pendingToolCallId) {
        migrated = true;
        const toolCallId = pendingToolCallId;
        pendingToolCallId = null;
        return { role: "tool", tool_call_id: toolCallId, content: message.content };
      }
      pendingToolCallId = null;
      return message;
    });
    if (migrated) {
      logger.info("aiplayer=%s: migrated legacy function_call history to tool_calls format", this.name);
    }
    return result;
  }

  async saveHistory() {
    if (this.debugging) {
      return;
    }
    const storage = await this.getStorage();
    const success = await storage.saveAIHistory(this.name, this.history);
    if (!success) {
      logger.error("Failed to save AI history for %s", this.name);
    }
  }

  filteredHistory() {
    // TODO: This is a hack to get the history to work. Improvements:
    // A summarizeHistory() method that uses the model to collapse early turns.
    // A tokenCount() function to make filteredHistory() smarter.
    // A rolling memory manager if you want to simulate long-term memory.
    return this.history;
  }

  handleWhisper(message) {
    this.handleMessage({ role: "system", content: message }).catch((error) =>
      logger.exception(error, "aiplayer=%s handleWhisper: error", this.name),
    );
  }

  tell(message, type = null) {
    if (this.sleeping) {
      return;
    }
    if (this.capturedMessages !== null) {
      this.capturedMessages.push(message);
    } else {
      const role = type === "whisper" ? "system" : "user";
      this.handleMessage({ role, content: message }).catch((error) =>
        logger.exception(error, "aiplayer=%s tell: error", this.name),
      );
    }
  }

  async handleMessage(message) {
    logger.debug("aiplayer=%s handleMessage: message=%s", this.name, JSON.stringify(message));
    if (!this.client) {
      logger.warning("aiplayer=%s handleMessage: message ignored: OpenAI api_key is not configured", this.name);
      return;
    }
    await this.historyPromise;
    this.history.push(message);
    let response;
    try {
      response = await this.generate();
    } catch (error) {
      logger.exception(error, "aiplayer=%s handleMessage: error", this.name);
      this.location.announce(this, `${this.name} appears to be offline.`, true);
      return;
    }
    await this.handleResponse(response);
  }

  async handleResponse(response) {
    if (response == null) {
      return;
    }
    // handle tool calls (formerly function calls)
    if (response.tool_calls?.length) {
      await this.handleToolCalls(response.tool_calls);
      return;
    }
    // handle content response
    const content = response.content;
    if (content == null) {
      return;
    }
    this.history.push({ role: "assistant", content });
    this.location.announce(this, content, true);
    await this.saveHistory();
  }

  async generate() {
    logger.debug(
      "aiplayer=%s generate: sending messages:\n%s",
      this.name,
      JSON.stringify(this.filteredHistory(), null, 2),
    );

    const tools = this.getTools();
    const params = { model: this.model, messages: this.filteredHistory() };
    if (tools) {
      params.tools = tools;
      params.tool_choice = "auto";
    }
    let response;
    try {
      response = await this.client.chat.completions.create(params);
    } catch (error) {
      if (error instanceof OpenAI.NotFoundError && String(error.message).toLowerCase().includes("tool use")) {
        logger.warning(
          "aiplayer=%s: Model %s doesn't support tools, falling back to text-only mode",
          this.name,
          this.model,
        );
        // Fallback to text-only mode
        this.useTools = false;
        response = await this.client.chat.completions.create({
          model: this.model,
          messages: this.filteredHistory(),
        });
        logger.debug("aiplayer=%s generate: response=%s", this.name, JSON.stringify(response));
        return response.choices?.[0]?.message ?? null;
      }
      // Re-throw if it's not a tool-related error
      throw error;
    }

    logger.debug("aiplayer=%s generate: response=%s", this.name, JSON.stringify(response));
    return response.choices?.[0]?.message ?? null;
  }

  getTools() {
    if (!this.useTools) {
      return null;
    }
    return [
      {
        type: "function",
        function: {
          name: "look",
          description: "Returns a description of the given object.",
          parameters: {
            type: "object",
            properties: {
              object: {
                type: "string",
                description:
                  'The object to look at, e.g. Ball, Jim. Use "here" for the current room, or "me" for yourself.',
              },
            },
            required: ["object"],
          },
        },
      },
      {
        type: "function",
        function: {
          name: "go",
          description: "Go in the given direction.",
          parameters: {
            type: "object",
            properties: {
              direction: {
                type: "string",
                description: "The direction to go, e.g. North",
              },
            },
            required: ["direction"],
          },
        },
      },
      {
        type: "function",
        function: {
          name: "name",
          description: "Sets the name of the given object.",
          parameters: {
            type: "object",
            properties: {
              object: {
                type: "string",
                description:
                  'The object to name, e.g. Ball, Jim. Use "here" for the current room, or "me" for yourself.',
              },
              name: {
                type: "string",
                description: "The new name of the object. The name should be a single word, no whitespace.",
              },
            },
            required: ["object", "name"],
          },
        },
      },
      {
        type: "function",
        function: {
          name: "describe",
          description: "Sets the description of the given object.",
          parameters: {
            type: "object",
            properties: {
              object: {
                type: "string",
                description:
                  'The object to describe, e.g. Ball, Jim. Use "here" for the current room, or "me" for yourself.',
              },
              description: {
                type: "string",
                description: "The new description of the object.",
              },
            },
            required: ["object", "description"],
          },
        },
      },
      {
        type: "function",
        function: {
          name: "dig",
          description: "Create a new room connected to the current room. This takes you into the newly created room.",
          parameters: {
            type: "object",
            properties: {
              direction: {
                type: "string",
                description:
                  "The direction from the current room to the new room, e.g. North, Up. An exit will be added to the current room with this name, which will take you to the new room.",
              },
              back: {
                type: "string",
                description:
                  "The reverse of the direction, e.g. South, Down. An exit will be added to the new room with this name, which will return you to the original room.",
              },
            },
            required: ["direction", "back"],
          },
        },
      },
      {
        type: "function",
        function: {
          name: "whisper",
          description: "Send a private message directly to another player.",
          parameters: {
            type: "object",
            properties: {
              player: {
                type: "string",
                description: "The name of the player to receive the message, e.g. Jim.",
              },
              message: {
                type: "string",
                description: "The private message to send to the player.",
              },
            },
            required: ["player", "message"],
          },
        },
      },
      {
        type: "function",
        function: {
          name: "take",
          description: "Pick up an object.",
          parameters: {
            type: "object",
            properties: {
              object: {
                type: "string",
                description: "The object to pick up, e.g. Ball. It must be in the current room.",
              },
            },
            required: ["object"],
          },
        },
      },
      {
        type: "function",
        function: {
          name: "drop",
          description: "Drop an object you are carrying.",
          parameters: {
            type: "object",
            properties: {
              object: {
                type: "string",
                description: "The object to drop, e.g. Ball. It must be in your inventory.",
              },
            },
            required: ["object"],
          },
        },
      },
      {
        type: "function",
        function: {
          name: "give",
          description: "Give an object you are carrying to another player.",
          parameters: {
            type: "object",
            properties: {
              player: {
                type: "string",
                description: "The name of the player to receive the object, e.g. Jim.",
              },
              object: {
                type: "string",
                description: "The object to give, e.g. Ball. It must be in your inventory.",
              },
            },
            required: ["player", "object"],
          },
        },
      },
      {
        type: "function",
        function: {
          name: "create",
          description: "Create a new object and add it to your inventory.",
          parameters: {
            type: "object",
            properties: {
              name: {
                type: "string",
                description: "The initial name of the new object. The name should be a single word, no whitespace.",
              },
            },
            required: ["name"],
          },
        },
      },
    ];
  }

  async handleToolCalls(toolCalls) {
    for (const toolCall of toolCalls) {
      const name = toolCall.function.name;
      const args = JSON.parse(toolCall.function.arguments);
      logger.debug("aiplayer=%s handleToolCall: name=%s arguments=%s", this.name, name, JSON.stringify(args));

      this.history.push({
        role: "assistant",
        content: null,
        tool_calls: [
          {
            id: toolCall.id,
            type: "function",
            function: { name: toolCall.function.name, arguments: toolCall.function.arguments },
          },
        ],
      });

      // Command execution is synchronous, so any output the command produces
      // via tell() lands in capturedMessages before we read it back out.
      this.capturedMessages = [];
      if (name === "go") {
        this.world.parseCommand(this, `go ${args.direction}`);
      } else if (name === "look") {
        this.world.parseCommand(this, `look ${args.object}`);
      } else if (name === "name") {
        this.world.parseCommand(this, `name ${args.object} as ${args.name}`);
      } else if (name === "describe") {
        this.world.parseCommand(this, `describe ${args.object} as ${args.description}`);
      } else if (name === "dig") {
        this.world.parseCommand(this, `dig ${args.direction} as ${args.back}`);
      } else if (name === "whisper") {
        this.world.parseCommand(this, `whisper ${args.player} ${args.message}`);
      } else if (name === "take") {
        this.world.parseCommand(this, `take ${args.object}`);
      } else if (name === "drop") {
        this.world.parseCommand(this, `drop ${args.object}`);
      } else if (name === "give") {
        this.world.parseCommand(this, `give ${args.object} to ${args.player}`);
      } else if (name === "create") {
        this.world.parseCommand(this, `create ${args.name}`);
      } else {
        this.capturedMessages.push("Function not found.");
      }
      let result = this.capturedMessages;
      this.capturedMessages = null;
      logger.debug("aiplayer=%s handleToolCall: result=%s", this.name, JSON.stringify(result));

      if (!result.length) {
        result = ["Success!"];
      }
      await this.handleMessage({ role: "tool", tool_call_id: toolCall.id, content: result.join("\n") });
    }
  }
}
registerClass("AIPlayer", AIPlayer);
