# MonkaMOO

A Python-based learning MOO (Multi-User Dungeon, Object Oriented) in the spirit of LambdaMOO, designed for family collaboration and learning.

## Features

- **Multi-player Support**: Multiple users can connect simultaneously
- **World Navigation**: Players can move between rooms and explore the virtual world
- **Object Creation**: Players can create and manipulate objects in the world
- **Communication**: Players can communicate via chat, whispers, and emotes
- **AI Players**: Integration with OpenAI API for AI-driven players
- **World Persistence**: World state is maintained between sessions
- **Multiple Interfaces**: Web interface, telnet server, and interactive shell
- **Cloud Storage**: Support for persistent storage on Heroku via AWS S3

## Quick Start

### Local Development

1. Clone the repository:

```bash
git clone <repository-url>
cd monkamoo
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

5. Start the web server:

```bash
python app.py
```

6. Or start the telnet server:

```bash
./moo -s
```

7. Or use the interactive shell:

```bash
./moo
```

### Heroku Deployment

1. Set up Heroku environment variables:

```bash
heroku config:set OPENAI_API_KEY=your_openai_api_key
heroku config:set STORAGE_TYPE=heroku
heroku config:set CLOUD_STORAGE_BUCKET=your-s3-bucket-name
heroku config:set AWS_ACCESS_KEY_ID=your-aws-access-key
heroku config:set AWS_SECRET_ACCESS_KEY=your-aws-secret-key
heroku config:set AWS_REGION=us-east-1
```

2. Deploy to Heroku:

```bash
git push heroku main
```

## Storage Configuration

MonkaMOO supports multiple storage backends for world state and AI player history:

### Local Storage (Default)

- Uses local files (`world.json` and `bots/*.json`)
- Suitable for development and testing
- No additional configuration required

### Cloud Storage (Heroku)

- Uses AWS S3 for persistent storage
- Required for Heroku deployment
- Configure with environment variables:
  - `STORAGE_TYPE=heroku`
  - `CLOUD_STORAGE_BUCKET=your-bucket-name`
  - `AWS_ACCESS_KEY_ID=your-key`
  - `AWS_SECRET_ACCESS_KEY=your-secret`
  - `AWS_REGION=us-east-1`

### Migration to Cloud Storage

To migrate your local data to S3:

1. **Set up your .env file** with AWS credentials and S3 bucket
2. **Run the migration script:**
   ```bash
   python migrate_to_cloud.py
   ```
3. **Deploy to Heroku** with the same environment variables

### Storage Fallback

The system automatically falls back to local storage if cloud storage is unavailable, ensuring the application continues to work even if S3 is temporarily unavailable.

## Environment Variables

- **OPENAI_API_KEY**: Required for AI player functionality
- **SECRET_KEY**: Web session security (default: 'JGS123#')
- **PORT**: Web server port (default: 5432)
- **TELNET_PORT**: Telnet server port (default: 8888)
- **STORAGE_TYPE**: Storage backend ('local' or 'heroku')
- **CLOUD_STORAGE_BUCKET**: S3 bucket name for cloud storage
- **AWS_ACCESS_KEY_ID**: AWS access key for S3
- **AWS_SECRET_ACCESS_KEY**: AWS secret key for S3
- **AWS_REGION**: AWS region (default: us-east-1)

## Commands

### Basic Commands

- `look` - Look around the current room
- `go north/south/east/west` - Move in a direction
- `say hello` - Say something to everyone in the room
- `whisper player message` - Send a private message
- `emote smiles` - Perform an action
- `take object` - Pick up an object
- `drop object` - Drop an object
- `give object to player` - Give an object to another player

### Advanced Commands

- `create flower as Object` - Create a new object
- `describe flower as "A beautiful red flower"` - Set object description
- `name flower as rose` - Set object name
- `dig north as "A dark tunnel"` - Create a new room
- `bot Poe` - Create an AI player
- `save` - Save the world state
- `load` - Reload the world state

## AI Players

You can add AI players to the MOO and give them roles or personalities.

### Setup

Configure your OpenAI API key:

```
cp .env.example .env
```

Edit `.env` and set the `OPENAI_API_KEY` value.

### Creating AI Players

In the MOO, type `bot [name]` to create an AI player. Then say something to it to give it an initial prompt.

### Notes

AI players have a set of functions available to them so they can take actions in the MOO, like
moving around, creating rooms and objects, and describing things. But they generally need to be told
to take these actions.

Some things we've found when experimenting with AI players:

1. A prompt like "You are the character Data from Star Trek." works really well.
1. If multiple bots get in the same room together, they'll happily keep talking to each other.
1. They sometimes get carried away with the narrative and will speak or emote for other players.

## Logging

The application uses a comprehensive logging system with the following components:

- **Web Server** (`monkamoo.web`): HTTP requests, WebSocket connections, user sessions
- **Telnet Server** (`monkamoo.server`): Client connections, command processing
- **Shell Interface** (`monkamoo.shell`): Interactive commands, user input
- **World Engine** (`monkamoo.world`): World loading/saving, object management
- **Player System** (`monkamoo.player`): Player actions, movements, interactions
- **AI Players** (`monkamoo.aiplayer`): OpenAI API calls, AI responses
- **Communication** (`monkamoo.broker`): Message publishing, subscriptions
- **Interpreter** (`monkamoo.interpreter`): Code execution, errors
- **Storage** (`monkamoo.storage`): File and cloud storage operations

### Example Log Output

```
2025-07-13 21:46:52 - monkamoo.web - INFO - Server starting on port 5432...
2025-07-13 21:46:52 - monkamoo.world - INFO - Loading world using storage abstraction
2025-07-13 21:46:52 - monkamoo.storage.factory - INFO - Initializing storage with type: local
2025-07-13 21:46:52 - monkamoo.world - INFO - World loaded successfully: 21 objects
2025-07-13 21:46:52 - monkamoo.web - INFO - WebSocket connection established for player: jim
2025-07-13 21:46:52 - monkamoo.player - INFO - Player jim creating object: flower as Object
2025-07-13 21:46:52 - monkamoo.world - INFO - Player jim successfully created object: flower
```

## References

- http://www.moo.mud.org
- https://www.hayseed.net/MOO/manuals/ProgrammersManual.html
- https://www.cc.gatech.edu/classes/cs8113e_99_winter/lambda.html
- https://github.com/wrog/lambdamoo
