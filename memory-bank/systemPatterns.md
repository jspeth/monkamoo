# System Patterns: MonkaMOO

## Architecture Overview

MonkaMOO follows a modular, object-oriented architecture with clear separation of concerns. As of August 2026 the implementation is Node.js (ESM, plain JavaScript); the retired Python implementation mirrors the same architecture.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │  Telnet Server  │    │ Interactive     │
│  (Express/ws)   │    │   (node:net)    │    │   Shell         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   World Engine  │
                    │ (src/core/*.js) │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Object System  │
                    │   (JS classes)  │
                    └─────────────────┘
```

## Core Design Patterns

### 1. **Object-Oriented MOO Pattern**

- **Purpose**: Represent everything in the world as objects
- **Implementation**: All game entities extend `Base` (`src/core/base.js`): `Room`, `Player`, `AIPlayer`, `Thing`, `Ball`
- **Note**: The class serialized as `"Object"` in world.json is named `Thing` in JS (the name `Object` collides with the JS built-in); the class registry maps the type name
- **Benefits**: Consistent interface, easy extension, natural programming model

```javascript
export class Base {
  constructor(props = {}) {
    this.id = randomUUID();
    this.world = null;
    this.name = null;
    this.description = null;
    this.location = null;
    this.contents = {};
    Object.assign(this, props);
  }
}
```

### 2. **Verb Dispatch Pattern**

- **Purpose**: Route parsed commands to methods on world objects
- **Implementation**: `World.findFunction` searches player → room → direct object → indirect object; `Base.getFunction(verb)` looks up `verb` or `do_verb` methods dynamically
- **Safety**: lookups skip anything on `Object.prototype` (`constructor`, `toString`, `__proto__`, ...) so players can't dispatch into JS internals
- **Benefits**: Verbs live on the objects they belong to; new objects bring their own verbs

### 3. **Class Registry Pattern** (replaces Python's `globals()` lookup)

- **Purpose**: Look up classes by name for world loading (`"type"` field) and the `create x as Class` command
- **Implementation**: `src/core/classRegistry.js` is a leaf module (no imports); each class module calls `registerClass(name, cls)` at definition time; `src/core/registry.js` imports all class modules to guarantee registration
- **Rationale**: avoids the ESM import cycle player → registry → aiplayer → player, which breaks under some import orders (TDZ on `extends Player`)

### 4. **Command Parser Pattern**

- **Purpose**: Parse natural-language commands into `verb / direct-object / preposition / indirect-object`
- **Implementation**: `src/lineParser.js` — word-splitting with article removal and a preposition synonym table (insertion order matters and matches the Python dict order)
- **Parity**: golden tests in `test/lineParser.test.js` were generated from the Python parser

### 5. **Event-Driven Communication Pattern**

- **Purpose**: Real-time updates across multiple interfaces
- **Implementation**: `src/broker.js` — per-channel (player name) sets of async message queues; WebSocket handlers subscribe and pump messages; `player.stdout` duck-typed writers (`{write, flush?}`) bridge game output to any interface
- **Benefits**: Responsive UI, multiple simultaneous clients per player

### 6. **World Persistence Pattern**

- **Purpose**: Save and restore world state
- **Implementation**: JSON serialization via `toJSON()` on each class; `sortedJSONStringify` (`src/utils.js`) reproduces Python's `json.dumps(sort_keys=True, indent=2)` **byte-for-byte** — this is the compatibility contract with the Python implementation and is enforced by a round-trip test
- **Structure**: flat `contents` map keyed by id; objects store `location` as an id, rebuilt into object references (and per-object `contents` maps) at load time

### 7. **Synchronous Command Execution** (load-bearing invariant)

- Command parse/dispatch (`World.parseCommand` → verb methods) is fully synchronous
- `AIPlayer.handleToolCalls` depends on this: it sets `capturedMessages = []`, runs a command, and collects everything the command told the player — this only works because no `await` occurs inside command execution
- Async boundaries live at the edges: AI API calls, storage I/O, broker delivery

## Key Technical Decisions

### 1. **JavaScript/Node.js as Core Language** (August 2026, supersedes Python)

- **Rationale**: one language across server and browser; Node's event loop natively matches the app's async model (the Python version was asyncio anyway); simpler deployment (no gunicorn/uvicorn layers)
- **Style**: plain JS + ESM, no TypeScript — keeps the family-learning accessibility goal

### 2. **Express + ws + Nunjucks for the Web Tier**

- Nunjucks reads the existing Jinja templates unchanged
- Sessions are a hand-rolled HMAC-SHA256 signed cookie (`monkamoo_session`) — small, dependency-free, verified during the WebSocket upgrade

### 3. **JSON for World Persistence**

- Human-readable, version-control friendly, no database dependency
- Format is frozen while the Python implementation remains in the tree

### 4. **Multiple Interface Support**

- Web (`server.js`), telnet (`src/telnetServer.js`), shell and JS REPL (`bin/moo.js`)
- All interfaces share `Shell`/`LineReader` or the broker; the world engine is interface-agnostic

## Component Relationships

- **`World`** (`src/core/world.js`): central coordinator — object registry, command parsing/dispatch, load/save via storage
- **`Player`** (`src/core/player.js`): user representation; most player verbs (look, jump, whisper, create, bot, help)
- **`AIPlayer`** (`src/core/aiplayer.js`): extends Player; OpenAI chat loop with tool calls that re-enter `world.parseCommand`
- **`Room`** (`src/core/room.js`): exits, announcements, look/go/dig/say/emote
- **`Thing`/`Ball`** (`src/core/thing.js`, `ball.js`): portable objects with take/drop/give (+ bounce/roll/throw)
- **Storage** (`src/storage/`): `LocalFileStorage`, `CloudStorage` (S3), async factory with health-check fallback

### Communication Flow

```
User Input → Parser → World Engine → Object Verbs →
tell()/announce() → player.stdout (stream or Broker) → Client Interface
```

## Extension Patterns

### Adding New Object Types

1. Create a class extending `Base` (or `Thing`) in `src/core/`
2. Set `static typeName` (the name used in world.json and `create ... as X`)
3. Call `registerClass(typeName, Class)` at the bottom of the module
4. Import the module from `src/core/registry.js`

### Adding New Commands

- Add a method named after the verb (or `do_verb`) to the class that should own it — the dispatch search path (player, room, objects) finds it automatically

### Adding New Interfaces

1. Produce lines of input and an object with `write()` for output
2. Either drive a `Shell` (stream-based interfaces) or call `world.parseCommand` directly and subscribe to the `Broker` (message-based interfaces)

## Security Patterns

- Verb dispatch is guarded against JS prototype internals (see pattern 2)
- Command handler exceptions are caught and reported, never crash the server
- Signed session cookies (HMAC-SHA256) with timing-safe comparison
- Otherwise a family-trust security model: no permissions system, no sandboxing (the interact REPL is intentionally full-power and only reachable from shell/telnet)
