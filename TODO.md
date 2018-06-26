TODO
----

* command aliases
* use introspection to look at verb args
  * inspect.getargspec
* exits point directly to room, not id?
* player << message shorthand for tell?
* live reload of object classes
* verb specifiers to restrict match
* interpreter locals: me, here
* save the world periodically
* player connected status (sleeping)
  * announce when connected
  * queue player messages offline
* "rooms" command
* "give" command
* emojis!
* security (hah)
* deployment

Done
----

* "find" command to find room that a player is in
* "jump" command (#room or @player)
* direct messages (/m or tell @player)
* interact over server
* change to generic location/contents properties
* objects
  * player/room contents
  * take/drop commands
  * verbs on objects
* parsing direct object and preposition
* better look up verbs on player, room, etc. (search path)
* adding "timer" for executing code after time has passed
* objects as containers
  * make Object use __contains__ etc.
  * player += object adds to contents
  * adding to contents adds to world
* add accept, on_exit, on_enter to move
