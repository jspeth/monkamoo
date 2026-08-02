// Importing these modules registers each class in the class registry.
// The "Object" type name maps to Thing (renamed to avoid the JS built-in).
import "./aiplayer.js";
import "./ball.js";
import "./base.js";
import "./player.js";
import "./room.js";
import "./thing.js";

export { getClass } from "./classRegistry.js";
