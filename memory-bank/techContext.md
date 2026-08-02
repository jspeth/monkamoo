# Technical Context: MonkaMOO

## Technology Stack

### Core Technologies

- **Node.js 20+**: Primary runtime (ported from Python in August 2026)
- **JavaScript (ESM)**: Plain modern JS, `"type": "module"`, no TypeScript
- **Express**: Web framework
- **ws**: WebSocket server for real-time communication
- **Nunjucks**: Template rendering (Jinja-compatible, reuses the original templates)
- **JSON**: World state persistence (`world.json`, `bots/*.json`)
- **node:net / node:repl / node:readline**: Telnet server, interact REPL, shell input

### History

- The original **Python implementation** was removed in August 2026 after the port merged and was verified in production. It's preserved at the **`python-final` git tag** (same world.json format, so the tagged version can still run against a copy of the world).

### Development Tools

- **npm**: Package management (`package.json`, `package-lock.json`)
- **Biome**: Linting and formatting (`biome.json`; 120-char lines, double quotes)
- **node:test**: Built-in test runner (no test dependencies)
- **Git**: Version control
- **direnv**: Automatic environment activation (optional)

### Deployment Technologies

- **Heroku**: Cloud deployment platform (`heroku/nodejs` buildpack)
- **Procfile**: `web: node server.js`
- **AWS S3**: Cloud persistence via `@aws-sdk/client-s3` when `STORAGE_TYPE=heroku`

## Development Environment Setup

```bash
# Clone and install (requires Node.js 20+)
git clone <repository-url>
cd monkamoo
npm install

# Environment variables
cp .env.example .env   # set OPENAI_API_KEY (and optionally OPENAI_BASE_URL, AI_MODEL)
```

### Running

```bash
npm start          # web server (http://localhost:5432)
./bin/moo.js       # interactive shell (default player: Jim)
./bin/moo.js -s    # telnet server (port 8888)
./bin/moo.js -i    # JS REPL with world + players in scope (.exit to leave)
```

### Environment Variables

#### AI Configuration

- **OPENAI_API_KEY**: Required for AI player functionality (works with OpenAI and OpenRouter)
- **OPENAI_BASE_URL**: Base URL for AI API (e.g., "https://openrouter.ai/api/v1" for OpenRouter)
- **AI_MODEL**: AI model to use (default: `o4-mini-2025-04-16`)
- **AI_USE_TOOLS**: Enable tool calling for AI players (default: true)

#### Server Configuration

- **SECRET_KEY**: Session-cookie signing key (default: 'JGS123#')
- **PORT**: Web server port (default: 5432)
- **TELNET_PORT**: Telnet server port (default: 8888)
- **LOG_LEVEL**: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)

#### Storage Configuration

- **STORAGE_TYPE**: 'local' (default) or 'heroku' (S3)
- **CLOUD_STORAGE_BUCKET**, **AWS_ACCESS_KEY_ID**, **AWS_SECRET_ACCESS_KEY**, **AWS_REGION**

## Dependencies (package.json)

```
express            # web framework
ws                 # WebSocket server
nunjucks           # templates (Jinja-compatible)
openai             # AI player API client
@aws-sdk/client-s3 # S3 cloud storage
dotenv             # .env loading

@biomejs/biome     # dev: lint + format
```

## Code Organization

```
monkamoo/
├── server.js            # Web server entry point (Express + ws)
├── bin/moo.js           # CLI entry point (shell / telnet / REPL)
├── src/
│   ├── core/            # World engine
│   │   ├── base.js      # Base class: ids, contents, move, verb lookup
│   │   ├── thing.js     # Portable objects (serialized as type "Object")
│   │   ├── ball.js      # Example object with verbs + timer
│   │   ├── room.js      # Rooms, exits, announcements
│   │   ├── player.js    # Players and most verbs
│   │   ├── aiplayer.js  # OpenAI-driven players with tool calls
│   │   ├── world.js     # Root container, load/save, command dispatch
│   │   ├── classRegistry.js # Leaf class registry (no imports)
│   │   └── registry.js  # Imports all classes to register them
│   ├── storage/         # local.js, cloud.js (S3), factory.js
│   ├── broker.js        # Pub/sub message queues for web clients
│   ├── lineParser.js    # Command parser (Preposition, Command, Parser)
│   ├── shell.js         # Shell + LineReader (stdin and telnet)
│   ├── telnetServer.js  # node:net server wrapping Shell
│   ├── interact.js      # node:repl wrapper
│   ├── logger.js        # Python-logging-style named loggers
│   └── utils.js         # joinStrings, stripChars, sortedJSONStringify
├── test/                # node:test suites + parser golden fixtures
├── templates/           # Nunjucks/Jinja templates (layout, login, session)
├── static/              # CSS
├── bots/                # AI player history (gitignored, runtime data)
└── world.json           # World state (format unchanged since the Python era)
```

## Testing

- **Framework**: `node:test` (built-in); run with `npm test`
- **Parser parity**: `test/lineParser.test.js` checks against golden values generated from the Python parser (`test/fixtures/parser-golden.json`)
- **Persistence parity**: `test/world.test.js` asserts `world.json` round-trips byte-for-byte through JS load/save
- **Command smoke tests**: in-memory world exercising look/dig/go/jump/create/take/drop/give/say/emote/whisper, plus the verb-dispatch security guard

## Code Quality & Linting

- **Biome** handles both linting and formatting: `npm run lint`, `npm run lint:fix`, `npm run format`
- **Makefile** mirrors npm scripts: `make lint`, `make test`, `make start`, `make moo`, `make server`, `make check-all`
- 120-character line width, double quotes, recommended lint rules (`noDelete` off — dynamic-key deletes are core to the contents-map design; `useNamingConvention` off — verb methods like `do_name` are a dispatch convention)

## Logging System

- `src/logger.js` mirrors the Python `logging_config` module: named loggers, `LOG_LEVEL` env var, printf-style interpolation
- **Modes**: `console` (stderr — web and telnet servers) and `file` (`log.txt` — interactive shell, so logs don't mix with game output)
- **Logger names unchanged from Python**: `monkamoo.web`, `monkamoo.server`, `monkamoo.shell`, `monkamoo.world`, `monkamoo.player`, `monkamoo.aiplayer`, `monkamoo.broker`, `monkamoo.storage.*`

## Technical Constraints

- **Single process, in-memory world**: state lives in one Node process; JSON persistence on explicit `save`
- **Persistence format is frozen** while the Python implementation remains: byte-compatible `world.json` is the contract
- **Synchronous command dispatch is load-bearing**: AIPlayer tool-call result capture depends on no `await` inside command execution
- **Family-trust security model**: no auth beyond a name, no sandboxing; interact REPL is full-power by design (shell/telnet only)

## Deployment

- **Heroku** (app: `monkamoo`, live at https://moo.speth.com): `git push heroku <branch>:main`; `heroku/nodejs` buildpack (set on the app with `heroku buildpacks:set` — app.json alone doesn't change existing apps) reads `package.json` engines (`>=20`) and runs the Procfile
- **npm registry**: the project `.npmrc` pins `registry.npmjs.org`. This is required — the dev machine's global `~/.npmrc` routes through a private work registry, and a lockfile generated against it breaks Heroku builds (npm E401). If `package-lock.json` ever shows `artifactory` URLs, regenerate it.
- **HTTPS**: Automatic Certificate Management is enabled for the custom domain
- **Cloud storage**: `STORAGE_TYPE=heroku` + AWS vars for S3-backed world/bot persistence with automatic local fallback (verified in production)
- **`bin/migrate-to-cloud.js`**: one-time local→S3 migration script (uploads world.json + bots/*.json, then verifies). Careful: it overwrites the cloud world with local data.
