import os
import sys
from tempfile import TemporaryDirectory

from click.testing import CliRunner

from tiny_listener import __version__
from tiny_listener.__main__ import main


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert result.output == f"tiny-listener {__version__}\n"


def test_cli_run_bad_app():
    runner = CliRunner()
    result = runner.invoke(main, ["bad:app"])
    assert result.exit_code == 1


def test_cli_run_ok():
    code = """
from tiny_listener import Listener

class FakeApp(Listener):
    async def listen(self): ...
    def run(self):
        print("Hello, World!")

app = FakeApp()
"""
    with TemporaryDirectory() as path:
        sys.path.insert(0, path)
        with open(os.path.join(path, "main.py"), "w") as f:
            f.write(code)

        runner = CliRunner()
        result = runner.invoke(main, ["main:app"])
        assert result.exit_code == 0
        assert result.output == "Hello, World!\n"
