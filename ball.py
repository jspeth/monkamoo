from core import Thing

class Ball(Thing):
    """ A simple ball. """

    def bounce(self, command):
        self.room.announce(command.player, 'The ball bounces up and down.')

    def roll(self, command):
        self.room.announce(command.player, 'The ball rolls away.')

    def throw(self, command):
        self.room.announce(command.player, 'The ball flies in the air.')
        def fall():
            self.room.announce(command.player, 'The ball falls to the ground, bounces a few times, then settles.')
        self.timer(5, fall)
