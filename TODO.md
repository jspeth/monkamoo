TODO
----

* make help dynamically generated
* import of player created classes
* better class finding for create
* command aliases
* use introspection to look at verb args
  * inspect.getargspec
* exits point directly to room, not id?
* player << message shorthand for tell?
* live reload of object classes
* verb specifiers to restrict match
* save the world periodically
* player connected status (sleeping)
  * announce when connected
  * queue player messages offline
* "rooms" command
* emojis!
* security (hah)

Done
----

* "give" command
* deployment
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
* interpreter locals: player names
* create command
