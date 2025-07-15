# Technical Context: MonkaMOO

## Technology Stack

### Core Technologies

- **Python 3.10+**: Primary programming language
- **Quart**: Async web framework (Flask-compatible)
- **WebSockets**: Real-time communication
- **JSON**: World state persistence
- **Socket Programming**: Telnet server implementation

### Web Technologies

- **HTML/CSS/JavaScript**: Frontend interface
- **WebSocket API**: Browser-based real-time communication
- **Session Management**: User authentication and state

### Development Tools

- **Git**: Version control
- **pip**: Python package management
- **venv**: Virtual environment isolation
- **direnv**: Automatic environment activation (optional)

### Deployment Technologies

- **Heroku**: Cloud deployment platform
- **Gunicorn**: WSGI server for production
- **Procfile**: Heroku process configuration
- **requirements.txt**: Python dependency specification

## Development Environment Setup

### Prerequisites

```bash
# Python 3.10 or higher
python --version

# Git for version control
git --version

# pip for package management
pip --version
```

### Local Development Setup

```bash
# Clone repository
git clone <repository-url>
cd monkamoo

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
# Optional: For OpenRouter support
echo "OPENAI_BASE_URL=https://openrouter.ai/api/v1" >> .env
echo "AI_MODEL=anthropic/claude-3.5-sonnet" >> .env
```

### Environment Variables

#### AI Configuration

- **OPENAI_API_KEY**: Required for AI player functionality (works with OpenAI and OpenRouter)
- **OPENAI_BASE_URL**: Base URL for AI API (e.g., "https://openrouter.ai/api/v1" for OpenRouter)
- **AI_MODEL**: AI model to use (e.g., "openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet")

#### Server Configuration

- **SECRET_KEY**: Web session security (default: 'JGS123#')
- **PORT**: Web server port (default: 5432)
- **TELNET_PORT**: Telnet server port (default: 8888)

## Dependencies

### Core Dependencies (requirements.txt)

```
quart>=0.18.4          # Async web framework
python-dotenv>=1.0.0   # Environment variable management
openai>=1.0.0          # OpenAI API integration
```

### Development Dependencies (requirements-dev.txt)

```
ruff>=0.1.0            # Fast Python linter (replaces flake8)
black>=23.0.0          # Code formatter
isort>=5.12.0          # Import sorting
mypy>=1.5.0            # Static type checking
pre-commit>=3.3.0      # Git hooks (optional)
pytest>=7.0.0          # Testing framework
pytest-asyncio>=0.21.0 # Async testing support
```

### Optional Dependencies

```
direnv>=2.30.0         # Automatic environment activation
heroku>=7.60.0         # Heroku CLI for deployment
```

## Architecture Components

### Web Interface (`app.py`)

- **Quart Application**: Main web server
- **WebSocket Support**: Real-time communication
- **Session Management**: User authentication
- **Template Rendering**: HTML interface

### Telnet Server (`server.py`)

- **Socket Programming**: Raw TCP connections
- **Command Processing**: Direct command execution
- **Multi-client Support**: Multiple simultaneous connections

### Interactive Shell (`shell.py`)

- **Python REPL**: Interactive development environment
- **World Integration**: Direct access to world objects
- **Debugging Support**: Development and testing tool

### Core Engine (`src/moo/`)

- **World Management**: Central game logic
- **Object System**: OOP-based entity management
- **Command Parser**: Natural language processing
- **Persistence**: State saving and loading

## Technical Constraints

### Performance Constraints

- **Single-threaded**: Python GIL limitations
- **Memory Usage**: JSON-based persistence limits scalability
- **Network Latency**: Real-time communication requirements
- **CPU Usage**: Command parsing overhead

### Scalability Constraints

- **Single Server**: No distributed architecture
- **File-based Storage**: No database backend
- **In-memory State**: Limited by available RAM
- **Connection Limits**: Socket connection limits

### Security Constraints

- **Simple Authentication**: No advanced security features
- **Code Execution**: Limited sandboxing
- **Input Validation**: Basic command validation
- **Family Safety**: Content filtering requirements

## Development Workflow

### Local Development

1. **Start Web Server**: `python app.py`
2. **Start Telnet Server**: `./moo -s`
3. **Interactive Shell**: `./moo`
4. **Testing**: Manual testing through interfaces

### Code Organization

```
monkamoo/
├── app.py              # Web application entry point
├── src/moo/           # Core engine
│   ├── core/          # Game objects and logic
│   ├── broker.py      # Communication system
│   ├── interpreter.py # Command interpretation
│   ├── line_parser.py # Command parsing
│   ├── server.py      # Telnet server
│   └── shell.py       # Interactive shell
├── templates/         # Web interface templates
├── static/           # Web assets
├── bots/             # AI player configurations
└── docs/             # Documentation
```

### Testing Strategy

- **Manual Testing**: Interactive testing through interfaces
- **Unit Testing**: Individual component testing
- **Integration Testing**: End-to-end functionality testing
- **User Testing**: Family-based usability testing

### Code Quality & Linting

- **Ruff**: Fast Python linter with auto-fix capabilities
- **Black**: Code formatter with 120-character line length
- **isort**: Import sorting compatible with Black
- **mypy**: Static type checking (optional but recommended)
- **VS Code Integration**: Real-time linting and formatting
- **Makefile Commands**: `make lint`, `make format`, `make fix`, `make type-check`
- **Configuration**: `pyproject.toml` for all tool settings
- **Line Length**: 120 characters across all tools

## Deployment Considerations

### Heroku Deployment

- **Buildpack**: Python buildpack
- **Process Types**: Web dyno for web interface
- **Environment Variables**: Configured via Heroku dashboard
- **Scaling**: Manual dyno scaling

### Local Deployment

- **Development Server**: `python app.py`
- **Production Server**: Gunicorn with UvicornWorker
- **Process Management**: Manual process management
- **Logging**: Standard output logging

## Monitoring and Debugging

### Logging System

- **Centralized Configuration**: `src/moo/logging_config.py` provides unified logging setup
- **Heroku Compatibility**: All logs output to stdout/stderr for `heroku logs` integration
- **Structured Format**: Consistent timestamp and module-based logging
- **Environment Configuration**: LOG_LEVEL environment variable support (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Module-Specific Loggers**: Each component has its own logger with appropriate namespacing

### Logging Components

- **Web Server**: `monkamoo.web` - HTTP requests, WebSocket connections, user sessions
- **Telnet Server**: `monkamoo.server` - Client connections, command processing
- **Shell Interface**: `monkamoo.shell` - Interactive commands, user input
- **World Engine**: `monkamoo.world` - World loading/saving, object management
- **Player System**: `monkamoo.player` - Player actions, movements, interactions
- **AI Players**: `monkamoo.aiplayer` - OpenAI API calls, AI responses
- **Communication**: `monkamoo.broker` - Message publishing, subscriptions
- **Interpreter**: `monkamoo.interpreter` - Code execution, errors

### Debugging Tools

- **Interactive Shell**: Direct world manipulation
- **Web Interface**: Visual debugging capabilities
- **Telnet Interface**: Command-line debugging
- **State Inspection**: JSON world state examination
- **Comprehensive Logs**: Detailed activity tracking across all components

## Future Technical Considerations

### Scalability Improvements

- **Database Backend**: PostgreSQL or MongoDB integration
- **Distributed Architecture**: Multi-server deployment
- **Caching Layer**: Redis for performance optimization
- **Load Balancing**: Multiple server instances

### Security Enhancements

- **Advanced Authentication**: OAuth or JWT-based auth
- **Code Sandboxing**: Safe code execution environment
- **Input Sanitization**: Comprehensive input validation
- **Rate Limiting**: Command execution throttling

### Performance Optimizations

- **Async Processing**: Background task processing
- **Connection Pooling**: Efficient client management
- **Caching Strategies**: Object and command caching
- **Compression**: Network traffic optimization
