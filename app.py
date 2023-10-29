#!/usr/bin/env python

import dotenv
from flask import Flask, render_template, redirect, request, session, url_for
from flask_socketio import SocketIO

from src.moo.core.player import Player
from src.moo.core.world import World

dotenv.load_dotenv()
world = World(path='world.json')
world.load()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'JGS123#'
socketio = SocketIO(app)

class SocketOutput(object):
    def __init__(self, player_name):
        self.player_name = player_name

    def write(self, data):
        socketio.emit(self.player_name, { 'message': data })

    def flush(self):
        pass

@app.route('/')
def index():
    if 'player_name' in session:
        return render_template('session.html', player_name=session['player_name'])
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        player_name = request.form['player_name']
        if player_name:
            player_name = player_name.lower()
        session['player_name'] = player_name
        player = world.find_player(player_name)
        if not player:
            player = Player(name=player_name)
            world.add_player(player)
        player.stdout = SocketOutput(player_name)
        return redirect(url_for('index'))
    return '''
        <form method="post">
            <p><input type=text name=player_name placeholder=Player>
            <p><input type=submit>
        </form>
    '''

@app.route('/logout')
def logout():
    session.pop('player_name', None)
    return redirect(url_for('index'))

@socketio.on('chat_event')
def handle_chat_event(json, methods=['GET', 'POST']):
    player_name = session.get('player_name')
    player = world.find_player(player_name)
    message = json.get('message')
    if player and message:
        world.parse_command(player, message)

if __name__ == '__main__':
    print('Server starting...')
    socketio.run(app, debug=True, port=5432)
