import assert from "node:assert/strict";
import fs from "node:fs";
import { test } from "node:test";
import { Player } from "../src/core/player.js";
import { World } from "../src/core/world.js";
import { sortedJSONStringify } from "../src/utils.js";

/** A Player stdout stub that collects everything the player is told. */
class CapturedOutput {
  constructor() {
    this.messages = [];
  }

  write(message) {
    this.messages.push(message);
  }

  flush() {}

  get text() {
    return this.messages.join("");
  }

  clear() {
    this.messages = [];
  }
}

test("world.json round-trips byte-for-byte through load and save", async () => {
  const original = fs.readFileSync("world.json", "utf8");
  const world = new World({ path: "world.json" });
  await world.load();
  const saved = sortedJSONStringify(world);
  assert.equal(saved, original);
});

function makeWorld() {
  const world = new World();
  const player = new Player({ name: "alice" });
  world.addPlayer(player);
  const output = new CapturedOutput();
  player.stdout = output;
  return { world, player, output };
}

test("look shows the room description", () => {
  const { world, player, output } = makeWorld();
  world.parseCommand(player, "look");
  assert.match(output.text, /This is the beginning of the world\./);
});

test("dig, go, and jump move the player between rooms", () => {
  const { world, player, output } = makeWorld();
  world.parseCommand(player, "dig north as south");
  assert.match(output.text, /alice created a room to the north\./);
  world.parseCommand(player, "go north");
  world.parseCommand(player, "name here as Attic");
  world.parseCommand(player, "go south");
  output.clear();
  world.parseCommand(player, "jump attic");
  world.parseCommand(player, "look");
  assert.match(output.text, /\*\*\* Attic \*\*\*/);
});

test("create, take, drop, and give work end to end", () => {
  const { world, player, output } = makeWorld();
  world.parseCommand(player, "create flower as Object");
  assert.match(output.text, /You created flower\./);

  world.parseCommand(player, "drop flower");
  assert.match(output.text, /You drop flower\./);
  world.parseCommand(player, "take flower");
  assert.match(output.text, /You take flower\./);

  const bob = new Player({ name: "bob" });
  world.addPlayer(bob);
  const bobOutput = new CapturedOutput();
  bob.stdout = bobOutput;
  world.parseCommand(player, "give flower to bob");
  assert.match(output.text, /You give flower to bob\./);
  assert.ok(bob.findThing("flower"));
});

test("create defaults to the Object class", () => {
  const { world, player, output } = makeWorld();
  world.parseCommand(player, "create pebble");
  assert.match(output.text, /You created pebble\./);
  assert.equal(JSON.parse(JSON.stringify(player.findThing("pebble"))).type, "Object");
});

test("say and emote announce to the room", () => {
  const { world, player, output } = makeWorld();
  const bob = new Player({ name: "bob" });
  world.addPlayer(bob);
  const bobOutput = new CapturedOutput();
  bob.stdout = bobOutput;
  world.parseCommand(player, "say hello");
  assert.match(bobOutput.text, /alice says, "hello"/);
  world.parseCommand(player, ":waves.");
  assert.match(bobOutput.text, /alice waves\./);
});

test("whisper between human players delivers privately", () => {
  const { world, player } = makeWorld();
  const bob = new Player({ name: "bob" });
  world.addPlayer(bob);
  const bobOutput = new CapturedOutput();
  bob.stdout = bobOutput;
  world.parseCommand(player, "@bob psst");
  assert.match(bobOutput.text, /alice whispers, "psst"/);
});

test("describe sets descriptions with original casing", () => {
  const { world, player, output } = makeWorld();
  world.parseCommand(player, "describe here as A room in the MOO.");
  assert.equal(player.location.description, "A room in the MOO.");
});

test("unknown commands are rejected politely", () => {
  const { world, player, output } = makeWorld();
  world.parseCommand(player, "frobnicate the widget");
  assert.match(output.text, /I didn't understand that\./);
});

test("JS object plumbing is not dispatchable as verbs", () => {
  const { world, player, output } = makeWorld();
  for (const verb of ["constructor", "toString", "hasOwnProperty", "__proto__"]) {
    output.clear();
    world.parseCommand(player, verb);
    assert.match(output.text, /I didn't understand that\./, `verb ${verb} should not dispatch`);
  }
});
