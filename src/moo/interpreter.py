import code
import contextlib
import io
import sys

from .logging_config import get_logger

# Get logger for this module
logger = get_logger("monkamoo.interpreter")


@contextlib.contextmanager
def stdout_io(stdout=None):
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
        if line == "":
            raise EOFError
        line = line.rstrip("\n\r")
        if line == "exit":
            logger.info("Interactive console received exit command")
            raise EOFError
        logger.debug("Interactive console input: %s", line)
        return line

    def runcode(self, code):
        logger.debug("Interactive console executing code: %s", code[:100] + "..." if len(code) > 100 else code)
        try:
            with stdout_io() as s:
                exec(code, self.locals)
            self.write(s.getvalue())
        except SystemExit:
            raise
        except Exception:
            logger.exception("Interactive console error")
            self.showtraceback()


def interact(banner=None, local=None, stdin=None, stdout=None):
    logger.info("Starting interactive console")
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    console = MOOInteractiveConsole(local, stdin=stdin, stdout=stdout)
    console.interact(banner)
