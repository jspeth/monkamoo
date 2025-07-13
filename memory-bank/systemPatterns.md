# System Patterns: MonkaMOO

## Architecture Overview

MonkaMOO follows a modular, object-oriented architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │  Telnet Server  │    │ Interactive     │
│   (Quart/WS)   │    │   (Socket)      │    │   Shell         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   World Engine  │
                    │   (Core Logic)  │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Object System  │
                    │  (Python OOP)   │
                    └─────────────────┘
```

## Core Design Patterns

### 1. **Object-Oriented MOO Pattern**
- **Purpose**: Represent everything in the world as objects
- **Implementation**: All game entities inherit from `base.Object`
- **Benefits**: Consistent interface, easy extension, natural programming model

```python
class Object:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.contents = []
        self.verbs = {}
    
    def add_verb(self, name, func):
        self.verbs[name] = func
```

### 2. **Command Parser Pattern**
- **Purpose**: Parse natural language commands into executable actions
- **Implementation**: `line_parser.py` with regex-based matching
- **Benefits**: Intuitive user interface, extensible command system

### 3. **Event-Driven Communication Pattern**
- **Purpose**: Real-time updates across multiple interfaces
- **Implementation**: `broker.py` with WebSocket support
- **Benefits**: Responsive UI, scalable to multiple clients

### 4. **World Persistence Pattern**
- **Purpose**: Save and restore world state
- **Implementation**: JSON-based serialization in `world.py`
- **Benefits**: State preservation, easy debugging, backup capability

## Key Technical Decisions

### 1. **Python as Core Language**
- **Decision**: Use Python for all core logic
- **Rationale**: 
  - Family-friendly and accessible
  - Rich ecosystem for web development
  - Easy to learn and teach
  - Strong object-oriented support
- **Trade-offs**: Performance vs. accessibility

### 2. **Async Web Framework (Quart)**
- **Decision**: Use Quart instead of Flask for async support
- **Rationale**:
  - WebSocket support for real-time communication
  - Async/await for better concurrency
  - Compatible with existing Python knowledge
- **Trade-offs**: Learning curve vs. performance benefits

### 3. **JSON for World Persistence**
- **Decision**: Use JSON for world state storage
- **Rationale**:
  - Human-readable format
  - Easy debugging and manual editing
  - No external database dependencies
  - Version control friendly
- **Trade-offs**: Performance vs. simplicity

### 4. **Multiple Interface Support**
- **Decision**: Support web, telnet, and shell interfaces
- **Rationale**:
  - Different user preferences
  - Accessibility for various technical levels
  - Development and debugging flexibility
- **Trade-offs**: Complexity vs. flexibility

## Component Relationships

### Core Components

#### `World` Class
- **Role**: Central coordinator and state manager
- **Responsibilities**:
  - Manage all objects and players
  - Handle command parsing and execution
  - Coordinate world persistence
  - Manage player connections

#### `Player` Class
- **Role**: Represents a user in the world
- **Responsibilities**:
  - Track player location and inventory
  - Handle player-specific commands
  - Manage communication channels
  - Store player state

#### `Room` Class
- **Role**: Represents locations in the world
- **Responsibilities**:
  - Manage room contents and exits
  - Handle room-specific verbs
  - Coordinate player movement
  - Manage room descriptions

#### `Object` Class
- **Role**: Base class for all world entities
- **Responsibilities**:
  - Provide common object functionality
  - Support verb system
  - Handle object relationships
  - Manage object state

### Communication Flow

```
User Input → Parser → World Engine → Object System → 
Response → Broker → Client Interface → User Output
```

## Design Principles

### 1. **Everything is an Object**
- All game entities inherit from `Object`
- Consistent interface across all entities
- Easy to extend with new object types

### 2. **Verb-Based Interaction**
- All interactions go through the verb system
- Natural language command parsing
- Extensible command vocabulary

### 3. **Separation of Concerns**
- Clear boundaries between components
- Minimal coupling between modules
- Easy to test and modify individual parts

### 4. **Family-Friendly Design**
- Simple, intuitive interfaces
- Safe experimentation environment
- Progressive complexity building

## Extension Patterns

### Adding New Object Types
1. Inherit from appropriate base class
2. Define object-specific verbs
3. Register with world system
4. Add to persistence system

### Adding New Commands
1. Define command function
2. Add to parser vocabulary
3. Register with appropriate objects
4. Update help system

### Adding New Interfaces
1. Implement interface-specific input/output
2. Connect to broker system
3. Handle session management
4. Integrate with world engine

## Performance Considerations

### Current Optimizations
- Lazy loading of object properties
- Efficient command parsing with regex
- Minimal state serialization
- Async I/O for web interface

### Future Optimization Opportunities
- Command caching for frequently used verbs
- Object property caching
- Database backend for large worlds
- Connection pooling for multiple clients

## Security Patterns

### Current Security Model
- Simple session-based authentication
- No permanent damage possible
- Safe object creation and modification
- Family-friendly content restrictions

### Security Considerations
- Input validation on all commands
- Safe code execution environment
- Rate limiting for commands
- Content filtering for family safety 