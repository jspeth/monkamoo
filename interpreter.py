import code
import contextlib
import io
import sys

@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = io.StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old


class MOOInteractiveConsole(code.InteractiveConsole):

    def __init__(self, locals=None, filename="<console>", stdin=None, stdout=None):
        code.InteractiveConsole.__init__(self, locals, filename)
        self.stdin = stdin
        self.stdout = stdout

    def write(self, data):
        self.stdout.write(data)
        self.stdout.flush()

    def raw_input(self, prompt=""):
        self.stdout.write(prompt)
        self.stdout.flush()
        line = self.stdin.readline()
        if line == '':
            raise EOFError
        line = line.rstrip('\n\r')
        if line == 'exit':
            raise EOFError
        return line

    def runcode(self, code):
        try:
            with stdoutIO() as s:
                exec(code, self.locals)
            self.write(s.getvalue())
        except SystemExit:
            raise
        except:
            self.showtraceback()


def interact(banner=None, local=None, stdin=None, stdout=None):
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    console = MOOInteractiveConsole(local, stdin=stdin, stdout=stdout)
    console.interact(banner)
