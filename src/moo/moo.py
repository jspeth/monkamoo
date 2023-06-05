#!/usr/bin/env python

import argparse

import interpreter
import server
import shell

from core.world import World

world = World(path='world.json')
world.load()

def main():
    parser = argparse.ArgumentParser(description='MonkaMOO')
    parser.add_argument('-i', '--interact', action='store_true', help='Run python shell')
    parser.add_argument('-s', '--server', action='store_true', help='Start moo server')
    args = parser.parse_args()
    if args.interact:
        globals().update(((p.name.lower()), p) for p in world.players)
        interpreter.interact(local=globals())
    elif args.server:
        print('Starting server...')
        moo_server = server.MonkaMOOServer(world)
        moo_server.run()
    else:
        me = world.find_player('Jim')
        shell.Shell(world, me).cmdloop()

if __name__ == '__main__':
    main()
