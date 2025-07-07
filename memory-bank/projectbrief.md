# Project Brief: MonkaMOO

## Vision
A Python-based learning MOO (Multi-User Dungeon, Object Oriented) in the spirit of LambdaMOO, designed for family collaboration and learning.

## Core Goals
1. **Family Collaboration**: Enable collaboration between family members (parent-child, grandparent-grandchild)
2. **Learning Platform**: Provide a safe environment for learning programming concepts through object-oriented design
3. **Text-Based Virtual Reality**: Create an immersive, multi-user text-based world
4. **Python Integration**: Allow coding MOO objects in Python and interacting with them in the world

## Key Requirements

### Functional Requirements
- **Multi-player Support**: Multiple users can connect simultaneously
- **World Navigation**: Players can move between rooms and explore the virtual world
- **Object Creation**: Players can create and manipulate objects in the world
- **Communication**: Players can communicate via chat, whispers, and emotes
- **AI Players**: Integration with OpenAI API for AI-driven players
- **World Persistence**: World state is maintained between sessions
- **Multiple Interfaces**: Web interface, telnet server, and interactive shell

### Technical Requirements
- **Python-Based**: Core implementation in Python for accessibility
- **Async Architecture**: Support for real-time communication via WebSockets
- **Extensible**: Easy to add new features and objects
- **Deployable**: Can be deployed to cloud platforms (Heroku)
- **Cross-Platform**: Works on multiple operating systems

### User Experience Requirements
- **Simple Interface**: Easy to use for non-technical family members
- **Intuitive Commands**: Natural language-like commands
- **Real-time Updates**: Immediate feedback for all actions
- **Safe Environment**: Appropriate for family use
- **Educational**: Encourages learning through exploration and creation

## Success Criteria
1. Family members can successfully connect and interact in the same virtual world
2. Users can create and manipulate objects using Python code
3. The system supports both synchronous and asynchronous play
4. The platform is stable and can handle multiple concurrent users
5. The learning curve is gentle enough for family members of varying technical backgrounds

## Constraints
- **Family-Friendly**: Content and interactions must be appropriate for all ages
- **Educational Focus**: Primary goal is learning, not entertainment
- **Python Ecosystem**: Leverage existing Python libraries and tools
- **Open Source**: Code should be accessible and modifiable 