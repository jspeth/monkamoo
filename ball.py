from core import Thing

class Ball(Thing):
    """ A simple ball. """

    def bounce(self, player):
        if self.room:
            self.room.announce(player, 'The ball bounces up and down.')

    def roll(self, player):
        if self.room:
            self.room.announce(player, 'The ball rolls away.')
