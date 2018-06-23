MonkaMOO
========

A Python-based learning MOO in the spirit of LambdaMOO.

Goal
----

To create a simple, multi-player, text-based virtual reality, that I can collaborate on with my daughter.

In addition to navigating, extending the world, and communicating with other players, you should be
able to code MOO objects in Python and interact with them in the world.

Running
-------

The MOO can be run locally for a single player or as a server for multiple players.

### Single player:

```
% ./moo.py
```

will start the MOO and connect a default player.

### Server:

```
% ./moo.py -s
```

will start the MOO server on port 8888.

Players should connect via telnet: `telnet localhost 8888`, then issue the `player` command to choose a player.

Common Commands
---------------

* `player [name]`: select an existing player or create a new one
* `look [object]`: show a description of the object or the current room
* `go [direction]`: change rooms by moving player in direction
* `jump [room name]`: go directly to a named room
* `dig [direction]`: create a new room, adding direction to the current room
* `name [name]`: set the current room name
* `describe [description]`: set the current room description
* `say [message]`: say a message to all players in the current room
* `emote [expression]`: express an action, feeling, or just about anything
* `whisper [player] [message]`: send a private message directly to another player
* `find [player]`: find player by name, gives their room name or description
* `take [object]`: pick up an object by name
* `drop [object]`: drop an object you are carrying

Shortcuts
---------

The following shortcuts can be used:

* `"` -- `say` (example: `"Hi there.` becomes `say Hi there.`)
* `:` -- `emote` (example: `:waves.` becomes `emote waves.`)
* `@` -- `whisper` (example: `@jim Psst...` becomes `whisper jim Psst...`)
* `#` -- `jump` (example: `#attic` becomes `jump attic`)

References
----------

* http://www.moo.mud.org
* https://www.hayseed.net/MOO/manuals/ProgrammersManual.html
* https://www.cc.gatech.edu/classes/cs8113e_99_winter/lambda.html
* https://github.com/wrog/lambdamoo
