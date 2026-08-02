# CLAUDE.md

MonkaMOO is a Node.js learning MOO (LambdaMOO-style multi-user text world) for family collaboration. Plain modern JavaScript (ESM), no TypeScript.

## Memory Bank — required reading

This project maintains its documentation of record in `memory-bank/`. **At the start of any non-trivial task, read `memory-bank/activeContext.md` and `memory-bank/progress.md`** — they hold the current focus, recent decisions, and what's left. Consult the others as the task requires:

- `projectbrief.md` — goals and requirements
- `productContext.md` — why the project exists, user experience goals
- `systemPatterns.md` — architecture, design patterns, extension recipes
- `techContext.md` — stack, commands, code layout, constraints

**Keep the memory bank current.** After completing significant work (new features, architectural changes, big refactors), update `activeContext.md` and `progress.md` to reflect the new state. When the user says **"update memory bank"**, review every file in `memory-bank/`, even ones that don't need changes. Write state as facts ("X works", "Y remains"), not session narrative.

`.cursor/rules/project-intelligence.mdc` mirrors the invariants below for Cursor sessions — keep the two in sync if invariants change.

## Critical invariants (violating these breaks things silently)

1. **`world.json` format is frozen.** `sortedJSONStringify` (src/utils.js) must produce byte-identical output to Python's `json.dumps(sort_keys=True, indent=2)`. The round-trip test in `test/world.test.js` enforces this — never weaken it. (A legacy Python implementation in `src/moo/` shares this file until it's retired.)
2. **Command dispatch must stay synchronous.** No `await` anywhere in `World.parseCommand` → verb methods. `AIPlayer.handleToolCalls` captures command output via `capturedMessages` between two synchronous statements.
3. **The class serialized as `"Object"` is named `Thing`** (`src/core/thing.js`) — `Object` collides with the JS built-in; the class registry maps the name.
4. **New world classes**: extend `Base`/`Thing`, set `static typeName`, call `registerClass(...)` at module bottom, add the import to `src/core/registry.js`. Never import `registry.js` from a class module (ESM cycle) — use `classRegistry.js`.
5. **Verb dispatch is security-guarded**: `Base.getFunction` skips `Object.prototype` members so players can't invoke `constructor`/`__proto__`/etc. Preserve this.

## Conventions

- Verb methods are named after what the player types (`look`, `dig`) or `do_verb` (`do_name`, `do_save`) — the snake_case is a dispatch convention, not a style slip.
- Logger names follow `monkamoo.*` (src/logger.js, printf-style interpolation).

## Commands

```bash
npm test             # node:test suite (28 tests; includes world.json round-trip)
npm run lint         # Biome check
npm start            # web server (Express + ws), http://localhost:5432
./bin/moo.js         # interactive shell   |  -s telnet server  |  -i JS REPL
```

Run `npm test` and `npm run lint` before considering any change done.

## Don'ts

- Don't modify the legacy Python implementation (`src/moo/`, `app.py`, `./moo`) — it's kept only for A/B comparison until retired; don't delete it unless asked.
- Don't commit `world.json` changes that came from running the game locally unless the user wants the world state saved.
- `bots/*.json` is runtime data (gitignored AI conversation histories) — never commit or hand-edit.
