MonkaMOO
========

A Python-based learning MOO in the spirit of LambdaMOO.

Goal
----

To create a simple, multi-player, text-based virtual reality, that I can collaborate on with my Dad or daughter.

In addition to navigating, extending the world, and communicating with other players, you should be
able to code MOO objects in Python and interact with them in the world.

Setup
-----

### First Time Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd monkamoo
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Automatic Environment Activation (Recommended)

To automatically activate the virtual environment when entering the project directory:

1. **Install direnv:**
   ```bash
   brew install direnv  # macOS
   # or: sudo apt install direnv  # Ubuntu/Debian
   ```

2. **Add direnv to your shell:**
   ```bash
   echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc  # For zsh
   # or: echo 'eval "$(direnv hook bash)"' >> ~/.bashrc  # For bash
   ```

3. **Restart your shell or run:**
   ```bash
   source ~/.zshrc  # or ~/.bashrc
   ```

4. **Allow the .envrc file:**
   ```bash
   direnv allow
   ```

Now when you `cd` into the project directory, the virtual environment will automatically activate (you'll see `(venv)` in your prompt).

### Manual Environment Activation

If you prefer to manually activate the environment:

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Environment Variables

Create a `.env` file and configure your OpenAI API key:

```bash
# Create .env file
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

Edit `.env` and set the `OPENAI_API_KEY` value for AI player functionality.

Deployment
----------

### Local Development

1. **Start the web server:**
   ```bash
   python app.py
   ```
   The MOO will be available at [http://127.0.0.1:5432](http://127.0.0.1:5432)

2. **Start the telnet server:**
   ```bash
   ./moo -s
   ```
   Players can connect via `telnet localhost 8888`

3. **Run the interactive shell:**
   ```bash
   ./moo
   ```
   Starts an interactive Python shell with the MOO world loaded.

### Heroku Deployment

The app is configured for Heroku deployment with the following files:

- **`Procfile`**: Configures Gunicorn with UvicornWorker for ASGI support
- **`runtime.txt`**: Specifies Python 3.10.5
- **`app.json`**: Heroku app configuration
- **`requirements.txt`**: Python dependencies

#### Deploy to Heroku:

1. **Install Heroku CLI** (if not already installed):
   ```bash
   brew install heroku/brew/heroku  # macOS
   # or visit: https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login to Heroku:**
   ```bash
   heroku login
   ```

3. **Create a new Heroku app:**
   ```bash
   heroku create your-moo-app-name
   ```

4. **Set environment variables:**
   ```bash
   heroku config:set OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Deploy the app:**
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

6. **Open the app:**
   ```bash
   heroku open
   ```

#### Alternative: Deploy via Heroku Dashboard

1. Connect your GitHub repository to Heroku
2. Set the `OPENAI_API_KEY` environment variable in the Heroku dashboard
3. Enable automatic deploys or deploy manually

#### Heroku App Structure

- **Web Dyno**: Runs the Quart web server on the port provided by Heroku
- **WebSocket Support**: Real-time communication via WebSockets
- **AI Players**: Configured to work with OpenAI API
- **Persistent World**: World state is maintained between sessions

Running
-------

The MOO can be run in several modes. See the **Deployment** section above for detailed instructions.

### Quick Start:

- **Web Interface**: `python app.py` → [http://127.0.0.1:5432](http://127.0.0.1:5432)
- **Telnet Server**: `./moo -s` → `telnet localhost 8888`
- **Interactive Shell**: `./moo` → Python shell with world loaded

Common Commands
---------------

* `player [name]`: select an existing player or create a new one
* `look [object]`: show a description of the object or the current room
* `go [direction]`: change rooms by moving player in direction
* `jump [room name]`: go directly to a named room
* `dig [direction]`: create a new room, adding direction to the current room
* `name [object] as [name]`: set an object's name
* `describe [object] as [description]`: set an object's description
* `say [message]`: say a message to all players in the current room
* `emote [expression]`: express an action, feeling, or just about anything
* `whisper [player] [message]`: send a private message directly to another player
* `find [player]`: find player by name, gives their room name or description
* `take [object]`: pick up an object by name
* `drop [object]`: drop an object you are carrying
* `give [object] to [player]`: give an object to another player
* `create [name] as [class]`: create a new object

Shortcuts
---------

The following shortcuts can be used:

* `"` -- `say` (example: `"Hi there.` becomes `say Hi there.`)
* `:` -- `emote` (example: `:waves.` becomes `emote waves.`)
* `@` -- `whisper` (example: `@jim Psst...` becomes `whisper jim Psst...`)
* `#` -- `jump` (example: `#attic` becomes `jump attic`)

AI Players
----------

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

References
----------

* http://www.moo.mud.org
* https://www.hayseed.net/MOO/manuals/ProgrammersManual.html
* https://www.cc.gatech.edu/classes/cs8113e_99_winter/lambda.html
* https://github.com/wrog/lambdamoo
