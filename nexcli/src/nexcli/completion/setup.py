import click
from click.shell_completion import get_completion_class
from ..cli import main as driver
from pathlib import Path
import os

CONFIG_PATH = Path.home() / ".nexcli"

@click.command(name="setup-completion")
@click.option(
    "-s", "--shell", type=click.Choice(("zsh",), case_sensitive=False), default="zsh"
)
def setup(shell: str):
    """Setup shell completion."""
    cls = get_completion_class(shell)
    comp = cls(driver, {}, "nex", "_NEX_COMPLETE")
    os.makedirs(CONFIG_PATH, exist_ok=True)
    script_path = CONFIG_PATH / f"nex-complete.{shell}"
    with open(script_path, "w") as file:
        file.write(comp.source())
    # Check if the ~/.zshrc is okay or not.
    instruction = f". ~/.nexcli/nex-complete.{shell}"
    rc_path = Path.home() / f".{shell}rc"
    if not os.path.isfile(rc_path):
        with open(rc_path, "w") as file:
            file.write(line)
    else:
        ready = False
        with open(rc_path, "r") as source:
            for line in source:
                if line.strip() == instruction:
                    ready = True
                    break
        if not ready:
            with open(rc_path, "a") as file:
                file.write("\n")
                file.write(instruction)
                file.write("\n")
    click.echo("Please restart your shell if it does not work.")
