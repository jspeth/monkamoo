#!/usr/bin/env python

import asyncio
import os
import sys

import dotenv
from quart import Quart, abort, redirect, render_template, request, session, url_for, websocket

# Configure logging BEFORE importing any modules that use logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from moo.logging_config import get_logger, setup_logging

# Set up console logging for web server
setup_logging(mode="console")

from src.moo.broker import Broker
from src.moo.core.player import Player
from src.moo.core.world import World

# Set up logger for this script
logger = get_logger("monkamoo.web")

dotenv.load_dotenv()
world = World(path="world.json")
world.load()

logger.info("World loaded successfully")

app = Quart(__name__)
app.config["SECRET_KEY"] = "JGS123#"
broker = Broker()


class SocketOutput:
    def __init__(self, player_name):
        self.player_name = player_name

    def write(self, message):
        asyncio.create_task(broker.publish(self.player_name, message))

    def flush(self):
        pass


async def _receive() -> None:
    while True:
        message = await websocket.receive()
        player_name = session.get("player_name")
        player = world.find_player(player_name)
        if player and message:
            logger.info("WebSocket message from %s: %s", player_name, message)
            world.parse_command(player, message)


@app.websocket("/ws")
async def ws() -> None:
    player_name = session.get("player_name")
    if not player_name:
        logger.warning("WebSocket connection attempt without player_name")
        abort(401)
    logger.info("WebSocket connection established for player: %s", player_name)
    try:
        task = asyncio.ensure_future(_receive())
        async for message in broker.subscribe(player_name):
            await websocket.send(message)
    except Exception as e:
        logger.exception("WebSocket error for player %s: %s", player_name, e)
    finally:
        task.cancel()
        await task
        logger.info("WebSocket connection closed for player: %s", player_name)


@app.route("/")
async def index():
    if "player_name" not in session:
        return redirect(url_for("login"))
    return await render_template("session.html", player_name=session["player_name"])


@app.route("/login", methods=["GET", "POST"])
async def login():
    if request.method == "POST":
        player_name = (await request.form)["player_name"]
        if player_name:
            player_name = player_name.lower()
        session["player_name"] = player_name
        logger.info("Player login: %s", player_name)
        player = world.find_player(player_name)
        if not player:
            player = Player(name=player_name)
            world.add_player(player)
            logger.info("New player created: %s", player_name)
        player.stdout = SocketOutput(player_name)
        return redirect(url_for("index"))
    return await render_template("login.html")


@app.route("/logout")
async def logout():
    player_name = session.get("player_name")
    session.pop("player_name", None)
    if player_name:
        logger.info("Player logout: %s", player_name)
    return redirect(url_for("index"))


if __name__ == "__main__":
    logger.info("Server starting on port 5432...")
    app.run(debug=True, port=5432)
