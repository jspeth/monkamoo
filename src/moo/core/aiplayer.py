import asyncio
import json
import logging
import openai
import os

from .player import Player
from ..line_parser import Command

# Use DEBUG for OpenAI API messages
# Use INFO for AIPLayer messages
# logging.basicConfig(filename='aiplayer.log', encoding='utf-8', level=logging.INFO)

class AIPlayer(Player):
    """ Represents an AI player in the MOO. """

    def __init__(self, api_key=None, **kwargs):
        super(AIPlayer, self).__init__(**kwargs)
        # Initialize OpenAI client with API key
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = openai.AsyncOpenAI(api_key=api_key) if api_key else None
        self.history_path = f'{self.name}.json'
        self.load_history()
        self.captured_messages = None
        self.sleeping = False

    def sleep(self, command):
        self.sleeping = True
        self.room.announce(self, '{name} goes to sleep.'.format(name=self.name), exclude_player=True)

    def wake(self, command):
        self.sleeping = False
        self.room.announce(self, '{name} wakes up.'.format(name=self.name), exclude_player=True)

    def load_history(self):
        try:
            data = open(self.history_path, 'r').read()
        except FileNotFoundError:
            data = None
        if not data:
            self.history = [
                {'role': 'system', 'content': f"Responses should be in the third person, like in a story, e.g. \"{self.name} says...\" or \"{self.name} looks around the room...\"."},
            ]
            return
        self.history = json.loads(data)

    def save_history(self):
        def serialize_tool_call(call):
            return {
                'id': call['id'],
                'type': call['type'],
                'function': {
                    'name': call['function']['name'],
                    'arguments': call['function']['arguments']
                }
            }

        def make_serializable(entry):
            # Deep copy to avoid mutating original
            entry = dict(entry)
            if 'tool_calls' in entry:
                entry['tool_calls'] = [serialize_tool_call(call) for call in entry['tool_calls']]
            return entry

        serializable_history = [make_serializable(msg) for msg in self.history]
        with open(self.history_path, 'w') as f:
            json.dump(serializable_history, f, indent=2, separators=(',', ': '))

    def filtered_history(self):
        # TODO: This is a hack to get the history to work. Improvements:
        # A summarize_history() method that uses GPT to collapse early turns.
        # A token_count() function using tiktoken to make filtered_history() smarter.
        # A rolling memory manager if you want to simulate long-term memory.
        return self.history

    def handle_whisper(self, message):
        asyncio.create_task(self.handle_message({'role': 'system', 'content': message}))

    def tell(self, message, type=None):
        if self.sleeping:
            return
        logging.info('aiplayer=%s tell: message="%s"', self.name, message)
        if self.captured_messages is not None:
            self.captured_messages.append(message)
        else:
            role = type == 'whisper' and 'system' or 'user'
            asyncio.create_task(self.handle_message({'role': role, 'content': message}))

    async def handle_message(self, message):
        logging.info('aiplayer=%s handle_message: message=%s', self.name, message)
        if not self.client:
            logging.info('aiplayer=%s handle_message: message ignored: OpenAI api_key is not configured', self.name)
            return
        self.history.append(message)
        try:
            response = await self.get_gpt()
        except Exception as err:
            logging.error('aiplayer=%s handle_message: error=%s', self.name, err)
            self.location.announce(self, f'{self.name} appears to be offline.', exclude_player=True)
            return
        await self.handle_response(response)

    async def handle_response(self, response):
        if response is None:
            return
        # handle tool calls (formerly function calls)
        if response.tool_calls:
            return await self.handle_tool_calls(response.tool_calls)
        # handle content response
        content = response.content
        if content is None:
            return
        self.history.append({'role': 'assistant', 'content': content})
        self.location.announce(self, content, exclude_player=True)
        self.save_history()

    async def get_gpt(self):
        logging.info('aiplayer=%s get_gpt: sending messages:\n%s', self.name, json.dumps(self.filtered_history(), indent=2))
        response = await self.client.chat.completions.create(
            model='o4-mini-2025-04-16',
            messages=self.filtered_history(),
            # max_tokens=50,
            # n=1,
            # stop=None,
            # temperature=0.8,
            tools=self.get_tools(),
            tool_choice='auto'
        )
        logging.info('aiplayer=%s get_gpt: response=%s', self.name, response)
        return response.choices and response.choices[0].message or None

    def get_tools(self):
        return [
            {
                'type': 'function',
                'function': {
                    'name': 'look',
                    'description': 'Returns a description of the given object.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'object': {
                                'type': 'string',
                                'description': 'The object to look at, e.g. Ball, Jim. Use "here" for the current room, or "me" for yourself.',
                            },
                        },
                        'required': ['object'],
                    },
                },
            },
            {
                'type': 'function',
                'function': {
                    'name': 'go',
                    'description': 'Go in the given direction.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'direction': {
                                'type': 'string',
                                'description': 'The direction to go, e.g. North',
                            },
                        },
                        'required': ['direction'],
                    },
                },
            },
            {
                'type': 'function',
                'function': {
                    'name': 'name',
                    'description': 'Sets the name of the given object.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'object': {
                                'type': 'string',
                                'description': 'The object to name, e.g. Ball, Jim. Use "here" for the current room, or "me" for yourself.',
                            },
                            'name': {
                                'type': 'string',
                                'description': 'The new name of the object. The name should be a single word, no whitespace.',
                            },
                        },
                        'required': ['object', 'name'],
                    },
                },
            },
            {
                'type': 'function',
                'function': {
                    'name': 'describe',
                    'description': 'Sets the description of the given object.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'object': {
                                'type': 'string',
                                'description': 'The object to describe, e.g. Ball, Jim. Use "here" for the current room, or "me" for yourself.',
                            },
                            'description': {
                                'type': 'string',
                                'description': 'The new description of the object.',
                            },
                        },
                        'required': ['object', 'description'],
                    },
                },
            },
            {
                'type': 'function',
                'function': {
                    'name': 'dig',
                    'description': 'Create a new room connected to the current room. This takes you into the newly created room.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'direction': {
                                'type': 'string',
                                'description': 'The direction from the current room to the new room, e.g. North, Up. An exit will be added to the current room with this name, which will take you to the new room.',
                            },
                            'back': {
                                'type': 'string',
                                'description': 'The reverse of the direction, e.g. South, Down. An exit will be added to the new room with this name, which will return you to the original room.',
                            },
                        },
                        'required': ['direction', 'back'],
                    },
                },
            },
            {
                'type': 'function',
                'function': {
                    'name': 'whisper',
                    'description': 'Send a private message directly to another player.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'player': {
                                'type': 'string',
                                'description': 'The name of the player to receive the message, e.g. Jim.',
                            },
                            'message': {
                                'type': 'string',
                                'description': 'The private message to send to the player.',
                            },
                        },
                        'required': ['player', 'message'],
                    },
                },
            },
            {
                'type': 'function',
                'function': {
                    'name': 'take',
                    'description': 'Pick up an object.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'object': {
                                'type': 'string',
                                'description': 'The object to pick up, e.g. Ball. It must be in the current room.',
                            },
                        },
                        'required': ['object'],
                    },
                },
            },
            {
                'type': 'function',
                'function': {
                    'name': 'drop',
                    'description': 'Drop an object you are carrying.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'object': {
                                'type': 'string',
                                'description': 'The object to drop, e.g. Ball. It must be in your inventory.',
                            },
                        },
                        'required': ['object'],
                    },
                },
            },
            {
                'type': 'function',
                'function': {
                    'name': 'give',
                    'description': 'Give an object you are carrying to another player.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'player': {
                                'type': 'string',
                                'description': 'The name of the player to receive the object, e.g. Jim.',
                            },
                            'object': {
                                'type': 'string',
                                'description': 'The object to give, e.g. Ball. It must be in your inventory.',
                            },
                        },
                        'required': ['player', 'object'],
                    },
                },
            },
            {
                'type': 'function',
                'function': {
                    'name': 'create',
                    'description': 'Create a new object and add it to your inventory.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'name': {
                                'type': 'string',
                                'description': 'The initial name of the new object. The name should be a single word, no whitespace.',
                            },
                        },
                        'required': ['name'],
                    },
                },
            },
        ]

    async def handle_tool_calls(self, tool_calls):
        for tool_call in tool_calls:
            name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            logging.info('aiplayer=%s handle_tool_call: name=%s arguments=%s', self.name, name, arguments)

            self.history.append({
                'role': 'assistant',
                'content': None,
                'tool_calls': [
                    {
                        'id': tool_call.id,
                        'type': 'function',
                        'function': {
                            'name': tool_call.function.name,
                            'arguments': tool_call.function.arguments
                        }
                    }
                ]
            })

            self.captured_messages = []
            if name == 'go':
                self.world.parse_command(self, 'go {direction}'.format(**arguments))
            elif name == 'look':
                self.world.parse_command(self, 'look {object}'.format(**arguments))
            elif name == 'name':
                self.world.parse_command(self, 'name {object} as {name}'.format(**arguments))
            elif name == 'describe':
                self.world.parse_command(self, 'describe {object} as {description}'.format(**arguments))
            elif name == 'dig':
                self.world.parse_command(self, 'dig {direction} as {back}'.format(**arguments))
            elif name == 'whisper':
                self.world.parse_command(self, 'whisper {player} {message}'.format(**arguments))
            elif name == 'take':
                self.world.parse_command(self, 'take {object}'.format(**arguments))
            elif name == 'drop':
                self.world.parse_command(self, 'drop {object}'.format(**arguments))
            elif name == 'give':
                self.world.parse_command(self, 'give {object} to {player}'.format(**arguments))
            elif name == 'create':
                self.world.parse_command(self, 'create {name}'.format(**arguments))
            else:
                self.captured_messages.append('Function not found.')
            result = self.captured_messages
            self.captured_messages = None
            logging.info('aiplayer=%s handle_tool_call: result=%s', self.name, result)

            if not result:
                result = ['Success!']
            await self.handle_message({'role': 'tool', 'tool_call_id': tool_call.id, 'content': '\n'.join(result)})
