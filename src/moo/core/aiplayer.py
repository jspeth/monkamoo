import asyncio
import json
import os

import openai

from src.moo.logging_config import get_logger
from src.moo.storage import get_storage_with_fallback

from .player import Player

# Get logger for this module
logger = get_logger("monkamoo.aiplayer")


class AIPlayer(Player):
    """Represents an AI player in the MOO."""

    def __init__(self, api_key=None, **kwargs):
        super().__init__(**kwargs)

        # Initialize AI client with API key and configuration
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        self.use_tools = os.getenv("AI_USE_TOOLS", "true").lower() == "true"
        self.model = os.getenv("AI_MODEL", "o4-mini-2025-04-16")

        if api_key:
            self.client = openai.AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
            )
            logger.info("aiplayer=%s: Created client with model %s", self.name, self.model)
        else:
            self.client = None
            logger.info("aiplayer=%s: No API key configured, AI functionality disabled", self.name)

        self.storage = get_storage_with_fallback()
        self.load_history()
        self.captured_messages = None
        self.sleeping = False
        self.debugging = False

    def debug(self, _command):
        self.debugging = not self.debugging
        self.room.announce(self, f"{self.name} debugging is now {self.debugging}.", exclude_player=True)

    def sleep(self, _command):
        self.sleeping = True
        self.room.announce(self, f"{self.name} goes to sleep.", exclude_player=True)

    def wake(self, _command):
        self.sleeping = False
        self.room.announce(self, f"{self.name} wakes up.", exclude_player=True)

    def load_history(self):
        history = self.storage.load_ai_history(self.name)
        if not history:
            self.history = [
                {
                    "role": "system",
                    "content": f'Responses should be in the third person, like in a story, e.g. "{self.name} says..." or "{self.name} looks around the room...".',
                },
            ]
            return
        self.history = history

    def save_history(self):
        if self.debugging:
            return

        def serialize_tool_call(call):
            return {
                "id": call["id"],
                "type": call["type"],
                "function": {"name": call["function"]["name"], "arguments": call["function"]["arguments"]},
            }

        def make_serializable(entry):
            # Deep copy to avoid mutating original
            entry = dict(entry)
            if "tool_calls" in entry:
                entry["tool_calls"] = [serialize_tool_call(call) for call in entry["tool_calls"]]
            return entry

        serializable_history = [make_serializable(msg) for msg in self.history]
        success = self.storage.save_ai_history(self.name, serializable_history)
        if not success:
            logger.error("Failed to save AI history for %s", self.name)

    def filtered_history(self):
        # TODO: This is a hack to get the history to work. Improvements:
        # A summarize_history() method that uses GPT to collapse early turns.
        # A token_count() function using tiktoken to make filtered_history() smarter.
        # A rolling memory manager if you want to simulate long-term memory.
        return self.history

    def handle_whisper(self, message):
        asyncio.create_task(self.handle_message({"role": "system", "content": message}))

    def tell(self, message, type=None):
        if self.sleeping:
            return
        logger.info('aiplayer=%s tell: message="%s"', self.name, message)
        if self.captured_messages is not None:
            self.captured_messages.append(message)
        else:
            role = type == "whisper" and "system" or "user"
            asyncio.create_task(self.handle_message({"role": role, "content": message}))

    async def handle_message(self, message):
        logger.info("aiplayer=%s handle_message: message=%s", self.name, message)
        if not self.client:
            logger.info("aiplayer=%s handle_message: message ignored: OpenAI api_key is not configured", self.name)
            return
        self.history.append(message)
        try:
            response = await self.get_gpt()
        except Exception:
            logger.exception("aiplayer=%s handle_message: error", self.name)
            self.location.announce(self, f"{self.name} appears to be offline.", exclude_player=True)
            return
        await self.handle_response(response)

    async def handle_response(self, response):
        if response is None:
            return None
        # handle tool calls (formerly function calls)
        if response.tool_calls:
            return await self.handle_tool_calls(response.tool_calls)
        # handle content response
        content = response.content
        if content is None:
            return None
        self.history.append({"role": "assistant", "content": content})
        self.location.announce(self, content, exclude_player=True)
        self.save_history()
        return None

    async def get_gpt(self):
        logger.info(
            "aiplayer=%s get_gpt: sending messages:\n%s",
            self.name,
            json.dumps(self.filtered_history(), indent=2),
        )

        tools = self.get_tools()
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=self.filtered_history(),
                tools=tools,
                tool_choice="auto" if tools else "none",
            )
        except openai.NotFoundError as e:
            if "tool use" in str(e).lower():
                logger.warning(
                    "aiplayer=%s: Model %s doesn't support tools, falling back to text-only mode",
                    self.name,
                    self.model,
                )
                # Fallback to text-only mode
                self.use_tools = False
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=self.filtered_history(),
                )
                logger.info("aiplayer=%s get_gpt: response=%s", self.name, response)
                return response.choices and response.choices[0].message or None
            # Re-raise if it's not a tool-related error
            raise

        logger.info("aiplayer=%s get_gpt: response=%s", self.name, response)
        return response.choices and response.choices[0].message or None

    def get_tools(self):
        if not self.use_tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": "look",
                    "description": "Returns a description of the given object.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "object": {
                                "type": "string",
                                "description": 'The object to look at, e.g. Ball, Jim. Use "here" for the current room, or "me" for yourself.',
                            },
                        },
                        "required": ["object"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "go",
                    "description": "Go in the given direction.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "direction": {
                                "type": "string",
                                "description": "The direction to go, e.g. North",
                            },
                        },
                        "required": ["direction"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "name",
                    "description": "Sets the name of the given object.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "object": {
                                "type": "string",
                                "description": 'The object to name, e.g. Ball, Jim. Use "here" for the current room, or "me" for yourself.',
                            },
                            "name": {
                                "type": "string",
                                "description": "The new name of the object. The name should be a single word, no whitespace.",
                            },
                        },
                        "required": ["object", "name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "describe",
                    "description": "Sets the description of the given object.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "object": {
                                "type": "string",
                                "description": 'The object to describe, e.g. Ball, Jim. Use "here" for the current room, or "me" for yourself.',
                            },
                            "description": {
                                "type": "string",
                                "description": "The new description of the object.",
                            },
                        },
                        "required": ["object", "description"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "dig",
                    "description": "Create a new room connected to the current room. This takes you into the newly created room.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "direction": {
                                "type": "string",
                                "description": "The direction from the current room to the new room, e.g. North, Up. An exit will be added to the current room with this name, which will take you to the new room.",
                            },
                            "back": {
                                "type": "string",
                                "description": "The reverse of the direction, e.g. South, Down. An exit will be added to the new room with this name, which will return you to the original room.",
                            },
                        },
                        "required": ["direction", "back"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "whisper",
                    "description": "Send a private message directly to another player.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "player": {
                                "type": "string",
                                "description": "The name of the player to receive the message, e.g. Jim.",
                            },
                            "message": {
                                "type": "string",
                                "description": "The private message to send to the player.",
                            },
                        },
                        "required": ["player", "message"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "take",
                    "description": "Pick up an object.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "object": {
                                "type": "string",
                                "description": "The object to pick up, e.g. Ball. It must be in the current room.",
                            },
                        },
                        "required": ["object"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "drop",
                    "description": "Drop an object you are carrying.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "object": {
                                "type": "string",
                                "description": "The object to drop, e.g. Ball. It must be in your inventory.",
                            },
                        },
                        "required": ["object"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "give",
                    "description": "Give an object you are carrying to another player.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "player": {
                                "type": "string",
                                "description": "The name of the player to receive the object, e.g. Jim.",
                            },
                            "object": {
                                "type": "string",
                                "description": "The object to give, e.g. Ball. It must be in your inventory.",
                            },
                        },
                        "required": ["player", "object"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create",
                    "description": "Create a new object and add it to your inventory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The initial name of the new object. The name should be a single word, no whitespace.",
                            },
                        },
                        "required": ["name"],
                    },
                },
            },
        ]

    async def handle_tool_calls(self, tool_calls):
        for tool_call in tool_calls:
            name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            logger.info("aiplayer=%s handle_tool_call: name=%s arguments=%s", self.name, name, arguments)

            self.history.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {"name": tool_call.function.name, "arguments": tool_call.function.arguments},
                        },
                    ],
                },
            )

            self.captured_messages = []
            if name == "go":
                self.world.parse_command(self, "go {direction}".format(**arguments))
            elif name == "look":
                self.world.parse_command(self, "look {object}".format(**arguments))
            elif name == "name":
                self.world.parse_command(self, "name {object} as {name}".format(**arguments))
            elif name == "describe":
                self.world.parse_command(self, "describe {object} as {description}".format(**arguments))
            elif name == "dig":
                self.world.parse_command(self, "dig {direction} as {back}".format(**arguments))
            elif name == "whisper":
                self.world.parse_command(self, "whisper {player} {message}".format(**arguments))
            elif name == "take":
                self.world.parse_command(self, "take {object}".format(**arguments))
            elif name == "drop":
                self.world.parse_command(self, "drop {object}".format(**arguments))
            elif name == "give":
                self.world.parse_command(self, "give {object} to {player}".format(**arguments))
            elif name == "create":
                self.world.parse_command(self, "create {name}".format(**arguments))
            else:
                self.captured_messages.append("Function not found.")
            result = self.captured_messages
            self.captured_messages = None
            logger.info("aiplayer=%s handle_tool_call: result=%s", self.name, result)

            if not result:
                result = ["Success!"]
            await self.handle_message({"role": "tool", "tool_call_id": tool_call.id, "content": "\n".join(result)})
