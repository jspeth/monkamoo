#!/usr/bin/env python

import argparse
import asyncio
import os
import sys

import dotenv

# Detect mode and configure logging BEFORE any src.moo imports
parser = argparse.ArgumentParser(description='MonkaMOO')
parser.add_argument('-i', '--interact', action='store_true', help='Run python shell')
parser.add_argument('-s', '--server', action='store_true', help='Start moo server')
args, unknown = parser.parse_known_args()

# Configure logging based on mode
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from moo.logging_config import get_logger, setup_logging

if args.interact or args.server:
    # Console logging for interactive Python shell and telnet server
    setup_logging(mode="console")
else:
    # File logging for interactive shell
    setup_logging(mode="file")

# Now import the rest of the app
from moo import interpreter, server, shell
from moo.core.world import World

dotenv.load_dotenv()

async def main():
    # Use the already-parsed args
    # Set up logger for this script
    logger = get_logger("monkamoo.main")
    
    world = World(path='world.json')
    world.load()
    logger.info("World loaded successfully")
    
    if args.interact:
        logger.info("Starting interactive Python shell")
        globals().update(((p.name.lower()), p) for p in world.players)
        interpreter.interact(local=globals())
    elif args.server:
        logger.info("Starting telnet server")
        moo_server = server.MonkaMOOServer(world)
        await moo_server.run()
    else:
        logger.info("Starting interactive shell")
        me = world.find_player('Jim')
        await shell.Shell(world, me).cmdloop()

if __name__ == '__main__':
    asyncio.run(main())
