import assert from "node:assert/strict";
import fs from "node:fs";
import { test } from "node:test";
import { Parser, Preposition } from "../src/lineParser.js";

// Golden values generated from the original Python implementation
// (src/moo/line_parser.py at the `python-final` tag) to pin parser behavior.
// Regenerate by checking out that tag and running Parser.parse over each line.
const golden = JSON.parse(fs.readFileSync(new URL("fixtures/parser-golden.json", import.meta.url), "utf8"));

for (const expected of golden) {
  test(`parses ${JSON.stringify(expected.line)} like the Python parser`, () => {
    const command = Parser.parse(expected.line);
    assert.equal(command.verb, expected.verb);
    assert.equal(command.directObjectStr, expected.directObjectStr);
    assert.equal(command.preposition, expected.preposition);
    assert.equal(command.indirectObjectStr, expected.indirectObjectStr);
    assert.deepEqual(command.args, expected.args);
    assert.equal(command.argsStr, expected.argsStr);
    assert.equal(command.indirectArgs, expected.indirectArgs);
  });
}

test("returns null for empty input", () => {
  assert.equal(Parser.parse(""), null);
  assert.equal(Parser.parse(null), null);
});

test("preposition synonyms map to canonical forms", () => {
  assert.equal(Parser.parse("give ball to jim").preposition, Preposition.AT);
  assert.equal(Parser.parse("put ball in box").preposition, Preposition.INTO);
  assert.equal(Parser.parse("ask about weather").preposition, Preposition.FOR);
});
