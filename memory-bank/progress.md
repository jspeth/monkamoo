# Progress: MonkaMOO

## What Works

### Node.js Port ✅ (August 2026 — current implementation)

- **Full port from Python to Node.js** on the `jspeth/node` branch, verified end-to-end:
  - Shell (`./bin/moo.js`), telnet (`./bin/moo.js -s`), web (`npm start`), JS REPL (`./bin/moo.js -i`)
  - AI players verified against the live OpenAI API (chat + tool-call plumbing)
  - 28 automated tests passing, including a byte-for-byte `world.json` round-trip and parser golden tests generated from the Python parser
- **Status**: committed on `jspeth/node` (PR/merge to master pending); Python implementation intentionally kept in-tree until the port is settled

### Core MOO Functionality ✅

- **Player Management**: Create, connect, and manage players
- **World Navigation**: Rooms, exits, go/jump, dig to create rooms
- **Object System**: create/take/drop/give, verbs on objects (Ball: bounce/roll/throw with timer)
- **Communication**: say, emote, whisper (with `"` `:` `@` `#` shortcuts)
- **World Persistence**: JSON save/load, format shared with the Python implementation
- **Command Parsing**: natural-language verb/object/preposition parsing with parity tests

### Multiple Interfaces ✅

- **Web Interface**: Express + ws + Nunjucks; signed-cookie sessions; auto-reconnecting chat UI (mobile-friendly)
- **Telnet Server**: `node:net`, multiple simultaneous clients
- **Interactive Shell**: stdin shell with player switching
- **Interact Mode**: live JavaScript REPL with `world` and players in scope

### AI Integration ✅

- **AI Players**: `openai` npm client; same 10 tool definitions as the Python version (look, go, name, describe, dig, whisper, take, drop, give, create)
- **OpenRouter Support**: `OPENAI_BASE_URL` + `AI_MODEL` env vars; text-only fallback for models without tool support
- **Bot Histories**: `bots/*.json` format unchanged; runtime `sleep`/`wake`/`debug`/`model` commands

### Storage System ✅

- **Local File Storage** and **AWS S3 Cloud Storage** behind a common async interface
- **Factory with health-check fallback** (`STORAGE_TYPE=heroku` → S3, falls back to local)
- **Byte-compatible serialization** with Python (`sortedJSONStringify`)

### Testing ✅ (new with the port)

- `node:test` suite: 28 tests — parser goldens, world round-trip, command smoke tests, verb-dispatch security guard
- `npm test` / `make test`

### Deployment ✅ (live in production)

- **Deployed to Heroku and verified**: live at https://moo.speth.com — world loads from S3, AI players active, login/WebSocket flows working
- Procfile: `web: node server.js`; `heroku/nodejs` buildpack set on the app (and in app.json); engines `node >= 20`
- Project `.npmrc` pins the public npm registry (the dev machine's global config uses a private work registry that broke Heroku builds with npm E401)
- **HTTPS enabled** on the custom domain via Heroku Automatic Certificate Management

### Code Quality ✅

- Biome lint + format, clean (`npm run lint`)
- Bugs fixed during the port: broken `create` class lookup, human-to-human whisper crash, fresh-world room 0 missing world ref, command exceptions killing caller tasks

## What's Left to Build

### Port Cleanup (near-term)

- **PR and merge** the port (`jspeth/node` → master)
- **Delete the Python implementation** once settled: `src/moo/`, `app.py`, `moo`, `requirements*.txt`, `pyproject.toml`, `venv/`, Python caches
- **Port or drop `migrate_to_cloud.py`** (still Python)

### High Priority TODO Items (carried over from TODO.md)

- **Dynamic Help System**: Generate help from the verb search path
- **Player-Created Classes**: Import/live-reload of player-coded object classes (now JS)
- **Command Aliases**: Shortcuts and aliases
- **Direct Room References**: Exits point to rooms, not ids
- **Periodic World Save**: Automatic state backup
- **Player Connection Status**: online/offline, announcements, offline message queue
- **"Rooms" Command**, **Emoji Support**

### Security and Safety Features

- Content filtering, input validation, rate limiting remain future work (family-trust model today)
- Verb-dispatch guard against JS prototype internals is done

### Test Coverage Growth

- Web routes and WebSocket flows, broker, AI tool-call loop with a mocked OpenAI client

## Current Status

- **Phase**: Node port complete and deployed → cleanup phase (merge to master, delete Python)
- **Stability**: All interfaces verified locally and in production (https://moo.speth.com)
- **Branch**: `jspeth/node`, deployed to Heroku from this branch
- **Known Issues**:
  - Python venv is broken (dangling pyenv symlink) — Python version needs venv recreation to run
  - Old Quart session cookies don't carry over (players re-login once)
  - `interact` REPL exits with `.exit` (not `exit` as in the Python version)

## Recent Achievements

### Node.js Port ✅ (August 2026)

- ~2,100 lines of Python ported to modern ESM JavaScript in one pass
- Byte-for-byte world.json compatibility maintained and test-enforced
- First automated test suite the project has had (28 tests)
- Four latent Python bugs fixed along the way

### Earlier (Python era)

- Storage abstraction + S3 migration ✅
- OpenRouter support ✅
- Modern chat web UI with mobile Safari support ✅
- Comprehensive logging system ✅
- Memory Bank documentation ✅

## Next Development Priorities

1. **PR + merge the port** (`jspeth/node` → master)
2. **Family play-testing** on the Node implementation (live at https://moo.speth.com)
3. **Remove Python code** once confidence is established
4. **Resume TODO.md features** in JavaScript (dynamic help first)
