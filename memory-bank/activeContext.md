# Active Context: MonkaMOO

## Current Work Focus

### Primary Objective

The **Python → Node.js port is complete**: merged to main (PR #18, August 2026), deployed to production, and the Python implementation has been removed from the tree (preserved at the `python-final` git tag). The project is now a pure Node.js codebase; focus shifts back to feature work.

### Immediate Goals

1. **Play-test the Node implementation** with real family usage (live at https://moo.speth.com)
2. **Resume TODO.md feature work** in JavaScript (dynamic help is the top item)

## Recent Changes

### Web UI Redesign ✅ COMPLETED (August 2026)

The web UI was redesigned from a chat-bubble look to a story-flow reading experience (August 2026):

- **Light, warm color scheme** (paper background, ink text, copper accent) via CSS custom properties in `static/style.css`; the old purple-gradient theme is gone
- **Two-panel layout**: large story panel on top (serif type, centered ~720px column, no bubbles), input at the bottom
- **Player commands** are echoed client-side as `.command-line` entries with a small uppercase player-name label; world output flows as `.story-line` paragraphs. Server messages carry no attribution yet — adding per-player indicators for *other* players' actions would need backend changes (possible future work)
- **Auto-growing textarea input** (grows to ~160px; Enter sends, Shift+Enter inserts a newline) with a send button for mobile
- Message text is now HTML-escaped client-side before insertion (the old code interpolated raw text into `innerHTML`)

### Python Implementation Removed ✅ COMPLETED (August 2026)

After the port merged to main (PR #18) and was verified in production, the Python implementation was deleted: `src/moo/`, `app.py`, `./moo`, `requirements*.txt`, `pyproject.toml`, `.python-version`, plus the broken venv and Python caches. The final Python revision is tagged **`python-final`**. The S3 migration script was ported to JS as `bin/migrate-to-cloud.js`. Docs, configs (biome.json, .gitignore, Makefile), CLAUDE.md, and the Cursor rules were scrubbed of Python references. The parser golden fixtures remain as the permanent record of the original parser's behavior.

### Heroku Deployment ✅ COMPLETED (August 2026)

The Node port is deployed and live at https://moo.speth.com (and http). Getting there required app-level config that `app.json` doesn't cover:

- **Buildpack switched** on the app: `heroku buildpacks:set heroku/nodejs` (the old Python buildpack built fine but the dyno crashed with `node: command not found`)
- **Public npm registry pinned**: the dev machine's global `~/.npmrc` routes through Squarespace's private Artifactory, so `package-lock.json` had private `resolved` URLs Heroku couldn't auth to (npm E401). A project-level `.npmrc` (`registry=https://registry.npmjs.org/`) overrides that permanently; lockfile regenerated
- **Automatic Certificate Management enabled** — `https://moo.speth.com` now works (previously the custom domain was HTTP-only)
- **Verified in production**: world loads from S3 (`STORAGE_TYPE=heroku`), AI players initialize with the configured OpenRouter model, login/session/static all serve correctly

### Node.js Port ✅ COMPLETED (August 2026)

The entire application was ported from Python to JavaScript. The decision: after developing in Python for a while, JS is a better fit (one language across server and browser front-end, event loop matches the app's async model).

- **Runtime/stack**: Node.js 20+, ESM modules, plain JavaScript (no TypeScript)
- **Web tier**: Express + `ws` + Nunjucks (replaces Quart); hand-rolled HMAC-signed session cookie (`monkamoo_session`) replaces Quart's session — old sessions don't carry over, players just re-login
- **Telnet server**: `node:net` (replaces asyncio streams)
- **Shell**: custom `LineReader` over stdin/socket streams (replaces cmd-style loop)
- **Interact mode**: `node:repl` — a live JS REPL with `world` and players in scope (exit with `.exit`)
- **AI players**: `openai` npm package, same tool definitions, same `bots/*.json` history format
- **Storage**: local FS + `@aws-sdk/client-s3`, same factory/fallback pattern
- **Tooling**: Biome (lint + format), `node:test` (28 tests), npm scripts + updated Makefile
- **Deploy**: Procfile is now `web: node server.js`; app.json uses `heroku/nodejs` buildpack

### Compatibility Contract

- **`world.json` and `bots/*.json` are shared between implementations.** `sortedJSONStringify` in `src/utils.js` reproduces Python's `json.dumps(sort_keys=True, indent=2)` byte-for-byte; a round-trip test enforces this. Either implementation can run against the same world.
- The Python class `Object` was renamed `Thing` in JS (collides with the JS built-in); the class registry maps the `"Object"` type name to it, so world.json is unchanged.

### Bugs Fixed During the Port

The port deliberately fixes four latent Python bugs:

1. **`create` was broken**: the `globals()` class lookup in `player.py` couldn't see the `Object` class (never imported there) — JS uses an explicit class registry
2. **Human-to-human whisper crashed**: `Player.tell(message)` was called with an extra `type` arg (TypeError in Python; harmless in JS)
3. **Fresh worlds were broken**: default room "0" never got its `world` reference, so `dig` crashed on a brand-new world
4. **Command exceptions could kill the caller's task**: `handleCommand` now catches, logs, and tells the player "Something went wrong."

Also added: verb-dispatch guard so `constructor`/`__proto__`/etc. can't reach JS object internals, and the web tier rebinds player output on every WebSocket connection (fixes lost output after server restart).

### Earlier Milestones (Python era)

- Modern chat web UI with mobile Safari support ✅
- OpenRouter support (`OPENAI_BASE_URL`, `AI_MODEL`) ✅
- Storage abstraction with S3 cloud storage and migration script ✅
- Comprehensive logging system ✅

## Current Project Status

### What's Working (verified end-to-end on the Node port)

- **All 28 tests pass**: parser golden tests (generated from the Python parser), world.json byte-for-byte round-trip, command smoke tests
- **Shell** (`./bin/moo.js`), **telnet** (`./bin/moo.js -s`), **web** (`npm start`) all verified interactively
- **AI players** verified against the live OpenAI API (bot created, replied, tool plumbing intact)
- **Interact REPL** (`./bin/moo.js -i`) works with world/players in scope

### What Needs Attention

- **Security**: same basic model as before (family-trust based)
- **TODO.md items** carry over unchanged (dynamic help, command aliases, periodic save, etc.)

## Active Decisions and Considerations

- **Plain JS, not TypeScript**: deliberate choice for accessibility and simplicity
- **Frozen persistence format**: `world.json` keeps the Python-era format (sorted keys, 2-space indent), enforced by the round-trip test — changing it now would only churn the file; revisit only with a real reason
- **Class self-registration pattern**: classes register in `src/core/classRegistry.js` (a leaf module) to avoid ESM import cycles; `src/core/registry.js` aggregates for entry points
- **Python history**: preserved at the `python-final` git tag; parser golden fixtures pin the original parser behavior

## Next Steps

### Immediate

1. Family play-testing on the Node implementation (live at https://moo.speth.com)

### Short Term

1. Grow the test suite (web routes, broker, AI tool-call loop with a mocked client)
2. Consider restructuring `src/` layout now that it's JS-only (optional)

### Medium Term

1. Resume TODO.md feature work in JS (dynamic help, command aliases, periodic world save, player connection status, rooms command, emojis)
2. Consider what "coding MOO objects" means in the JS world — the interact REPL is the seed of this
