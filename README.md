MonkaMOO
========

A Python-based learning MOO in the spirit of LambdaMOO.

Goal
----

To create a simple, multi-player, text-based virtual reality, that I can collaborate on with my Dad or daughter.

In addition to navigating, extending the world, and communicating with other players, you should be
able to code MOO objects in Python and interact with them in the world.

Running
-------

Install dependencies:

```
% pip install -r requirements.txt
```

The MOO can be run locally for a single player or as a server for multiple players.

### Single player:

```
% ./moo
```

will start the MOO and connect a default player.

### Telnet Server:

```
% ./moo -s
```

will start the MOO telnet server on port 8888.

Players should connect via telnet: `telnet localhost 8888`, then issue the `player` command to choose a player.

### Web Server:

```
% ./app.py
```

will start the MOO web server at [http://127.0.0.1:5432](http://127.0.0.1:5432)

Common Commands
---------------

* `player [name]`: select an existing player or create a new one
* `look [object]`: show a description of the object or the current room
* `go [direction]`: change rooms by moving player in direction
* `jump [room name]`: go directly to a named room
* `dig [direction]`: create a new room, adding direction to the current room
* `name [object] as [name]`: set an object's name
* `describe [object] as [description]`: set an object's description
* `say [message]`: say a message to all players in the current room
* `emote [expression]`: express an action, feeling, or just about anything
* `whisper [player] [message]`: send a private message directly to another player
* `find [player]`: find player by name, gives their room name or description
* `take [object]`: pick up an object by name
* `drop [object]`: drop an object you are carrying
* `give [object] to [player]`: give an object to another player
* `create [name] as [class]`: create a new object

Shortcuts
---------

The following shortcuts can be used:

* `"` -- `say` (example: `"Hi there.` becomes `say Hi there.`)
* `:` -- `emote` (example: `:waves.` becomes `emote waves.`)
* `@` -- `whisper` (example: `@jim Psst...` becomes `whisper jim Psst...`)
* `#` -- `jump` (example: `#attic` becomes `jump attic`)

AI Players
----------

You can add AI players to the MOO and give them roles or personalities.

### Setup

Configure your OpenAI API key:

```
cp .env.example .env
```

Edit `.env` and set the `OPENAI_API_KEY` value.

### Creating AI Players

In the MOO, type `bot [name]` to create an AI player. Then say something to it to give it an initial prompt.

### Notes

AI players have a set of functions available to them so they can take actions in the MOO, like
moving around, creating rooms and objects, and describing things. But they generally need to be told
to take these actions.

Some things we've found when experimenting with AI players:

1. A prompt like "You are the character Data from Star Trek." works really well.
1. If multiple bots get in the same room together, they'll happily keep talking to each other.
1. They sometimes get carried away with the narrative and will speak or emote for other players.

References
----------

* http://www.moo.mud.org
* https://www.hayseed.net/MOO/manuals/ProgrammersManual.html
* https://www.cc.gatech.edu/classes/cs8113e_99_winter/lambda.html
* https://github.com/wrog/lambdamoo
