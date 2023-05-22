import asyncio
import json
import openai
import os
import threading

from .player import Player
from line_parser import Command

class AIPlayer(Player):
    """ Represents an AI player in the MOO. """

    def __init__(self, api_key=None, **kwargs):
        super(AIPlayer, self).__init__(**kwargs)
        openai.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.history_path = f'{self.name}.json'
        self.load_history()

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
        data = json.dumps(self.history, indent=2, separators=(',', ': '))
        with open(self.history_path, 'w') as f:
            f.write(data)

    def tell(self, message):
        thread = threading.Thread(target=self.run_async, args=(message,))
        thread.start()

    def run_async(self, message):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.handle_message(message))

    async def handle_message(self, message):
        self.history.append({'role': 'user', 'content': message})
        try:
            response = await self.get_gpt()
        except Exception as err:
            print('JGS - error:', err)
            self.location.announce(self, f'{self.name} appears to be offline.', exclude_player=True)
            return
        if response is not None:
            self.history.append({'role': 'assistant', 'content': response})
            self.location.announce(self, response, exclude_player=True)
            self.save_history()

    async def get_gpt(self):
        response = await openai.ChatCompletion.acreate(
            model='gpt-3.5-turbo',
            messages=self.history,
            # max_tokens=50,
            # n=1,
            # stop=None,
            temperature=0.8
        )
        return response.choices and response.choices[0].message.content or None

    def create(self, command):
        # Override the create method to prevent AIPlayer from creating objects
        self.tell("Sorry, I don't have the ability to create objects.")

    def dig(self, command):
        # Override the dig method to prevent AIPlayer from digging new rooms
        self.tell("Sorry, I don't have the ability to dig new rooms.")

    def take(self, command):
        # Override the take method to prevent AIPlayer from taking objects
        self.tell("Sorry, I don't have the ability to take objects.")

    def drop(self, command):
        # Override the drop method to prevent AIPlayer from dropping objects
        self.tell("Sorry, I don't have the ability to drop objects.")

    def whisper(self, command):
        # Override the whisper method to prevent AIPlayer from whispering to other players
        self.tell("Sorry, I don't have the ability to whisper to other players.")
