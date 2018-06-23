import moo

class Preposition(object):

    WITH = 'with'
    AT = 'at'
    IN_FRONT = 'in_front'
    INTO = 'into'
    ONTO = 'onto'
    FROM = 'from'
    OVER = 'over'
    THROUGH = 'through'
    UNDER = 'under'
    BEHIND = 'behind'
    BESIDE = 'beside'
    FOR = 'for'
    IS = 'is'
    AS = 'as'
    OFF = 'off'

    keys = {
        'with': WITH,
        'using': WITH,
        'at': AT,
        'to': AT,
        'in front of': IN_FRONT,
        'in': INTO,
        'inside': INTO,
        'into': INTO,
        'on top of': ONTO,
        'on': ONTO,
        'onto': ONTO,
        'upon': ONTO,
        'out of': FROM,
        'from inside': FROM,
        'from': FROM,
        'over': OVER,
        'through': THROUGH,
        'under': UNDER,
        'underneath': UNDER,
        'beneath': UNDER,
        'behind': BEHIND,
        'beside': BESIDE,
        'for': FOR,
        'about': FOR,
        'is': IS,
        'as': AS,
        'off': OFF,
        'off of': OFF
    }


class Command(object):

    def __init__(self, verb=None, direct_object_str=None, preposition=None, indirect_object_str=None):
        self.player = None
        self.verb = verb
        self.direct_object = None
        self.direct_object_str = direct_object_str
        self.preposition = preposition
        self.indirect_object = None
        self.indirect_object_str = indirect_object_str

    def __repr__(self):
        return '<Command verb={verb} dobj={direct_object} prep={preposition} iobj={indirect_object}>'.format(**self.__dict__)

    def resolve(self, player):
        """ Identify direct and indirect objects in the command relative to player.

        Varies from LambdaMOO slightly:
            '@name' identifies player by name
            '#room' identifies a room by name
            '$uuid' identifies an object by id

        Otherwise it looks for the objects in the player contents then the player's room contents.
        """
        def resolve_object(name):
            if not name:
                return None
            name = name.lower()
            if name == 'me':
                return player
            if name == 'here':
                return player.location
            if name.startswith('@'):
                return moo.world.find_player(name.strip('@'))
            if name.startswith('#'):
                return moo.world.find_room(name.strip('#'))
            if name.startswith('$'):
                return moo.world.contents.get(name.strip('$'))
            for obj in player.contents.values() + player.location.contents.values():
                if obj.name.lower() == name:
                    return obj
            return None
        self.player = player
        self.direct_object = resolve_object(self.direct_object_str)
        self.indirect_object = resolve_object(self.indirect_object_str)


class Parser(object):
    """ MOO command parser.

    Structure:
        verb
        verb direct-object
        verb direct-object preposition indirect-object

    Examples:
        look
        take yellow bird
        put yellow bird in cuckoo clock
    """

    articles = ['a', 'an', 'the']

    @classmethod
    def parse(cls, line):
        """ Parse a line of text into a MOO command. """
        if not line:
            return None
        # split line into words
        words = line.split(' ')
        words = [w for w in words if w.lower() not in Parser.articles]
        if not words:
            return None
        # verb is always the first word
        verb = words[0].lower()
        if len(words) == 1:
            return Command(verb)
        # find preposition
        i = 1
        preposition = None
        for w in words[1:]:
            preposition = Preposition.keys.get(w.lower())
            if preposition:
                break
            i += 1
        # find objects
        direct_object = None
        indirect_object = None
        if preposition:
            direct_object = ' '.join(words[1:i]) or None
            indirect_object = ' '.join(words[i + 1:]) or None
        else:
            direct_object = ' '.join(words[1:])
        # return command
        return Command(verb, direct_object, preposition, indirect_object)


if __name__ == '__main__':
    tests = [
        'look',
        'look me',
        'look at sky',
        'look at',
        'take ball',
        'take ball at',
        'look under rock',
        'hide ball under sand',
        'put yellow bird in cuckoo clock'
    ]
    for line in tests:
        command = Parser.parse(line)
        print '{line} -> [verb={verb} dobj={dobj} prep={prep} iobj={iobj}]'.format(
            line=`line`,
            verb=`command.verb`,
            dobj=`command.direct_object_str`,
            prep=`command.preposition`,
            iobj=`command.indirect_object_str`
        )
