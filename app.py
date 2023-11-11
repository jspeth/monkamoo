#!/usr/bin/env python

import asyncio
import dotenv
from quart import Quart, abort, render_template, redirect, request, session, url_for, websocket

from src.moo.broker import Broker
from src.moo.core.player import Player
from src.moo.core.world import World

dotenv.load_dotenv()
world = World(path='world.json')
world.load()

app = Quart(__name__)
app.config['SECRET_KEY'] = 'JGS123#'
broker = Broker()

class SocketOutput(object):
    def __init__(self, player_name):
        self.player_name = player_name

    def write(self, message):
        asyncio.create_task(broker.publish(self.player_name, message))

    def flush(self):
        pass

async def _receive() -> None:
    while True:
        message = await websocket.receive()
        player_name = session.get('player_name')
        player = world.find_player(player_name)
        if player and message:
            world.parse_command(player, message)

@app.websocket('/ws')
async def ws() -> None:
    player_name = session.get('player_name')
    if not player_name:
        abort(401)
    try:
        task = asyncio.ensure_future(_receive())
        async for message in broker.subscribe(player_name):
            await websocket.send(message)
    finally:
        task.cancel()
        await task

@app.route('/')
async def index():
    if 'player_name' not in session:
        return redirect(url_for('login'))
    return await render_template('session.html', player_name=session['player_name'])

@app.route('/login', methods=['GET', 'POST'])
async def login():
    if request.method == 'POST':
        player_name = (await request.form)['player_name']
        if player_name:
            player_name = player_name.lower()
        session['player_name'] = player_name
        player = world.find_player(player_name)
        if not player:
            player = Player(name=player_name)
            world.add_player(player)
        player.stdout = SocketOutput(player_name)
        return redirect(url_for('index'))
    return await render_template('login.html')

@app.route('/logout')
async def logout():
    session.pop('player_name', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    print('Server starting...')
    app.run(debug=True, port=5432)
