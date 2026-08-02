/**
 * Class registry used wherever the Python implementation looked classes up in
 * `globals()`: loading world.json ("type" field) and the `create ... as X`
 * command. This module has no imports so any class module can use it without
 * creating an ESM cycle; classes register themselves at definition time, and
 * registry.js aggregates them all for entry points.
 */
const classes = {};

export function registerClass(name, cls) {
  classes[name] = cls;
}

export function getClass(name) {
  return Object.hasOwn(classes, name) ? classes[name] : null;
}
