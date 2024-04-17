from typing import Optional
from .transformer import Transformer

import click


@click.group(chain=True)
@click.option("--input", "-i", type=click.STRING, default=None)
@click.pass_context
def cli(ctx: click.Context, input: Optional[str]) -> None:
    """Transform images using subcommands."""
    ctx.ensure_object(Transformer)
    transformer: Transformer = ctx.obj
    transformer.load(input, Transformer.DEFAULT_SRC)


@cli.command()
@click.argument("path", type=click.STRING)
@click.option("--dst", "-d", type=click.STRING, default="img")
@click.pass_context
def load(ctx: click.Context, path: str, dst: str) -> None:
    """Load an image to dst."""
    transformer: Transformer = ctx.obj
    transformer.load(path, dst)


@cli.command()
@click.argument("path", type=click.STRING)
@click.option("--src", "-s", type=click.STRING, default="img")
@click.pass_context
def save(ctx: click.Context, path: str, src: str):
    """Save an image from src to a file."""
    transformer: Transformer = ctx.obj
    transformer.save(path, src)


@cli.command()
@click.option("--src", "-s", type=click.STRING, default="img")
@click.option("--dst", "-d", type=click.STRING, default="img")
@click.pass_context
def clone(ctx: click.Context, src: str, dst: str):
    """Clone an image from src to dst."""
    transformer: Transformer = ctx.obj
    transformer.clone(src, dst)


@cli.command()
@click.option("--width", "-w", type=click.IntRange(min=-1), default=-1)
@click.option("--height", "-h", type=click.IntRange(min=-1), default=-1)
@click.option(
    "--algorithm",
    "-a",
    type=click.Choice(
        ("auto", "linear", "nearest", "cubic", "area"), case_sensitive=False
    ),
    default="auto",
)
@click.option("--src", "-s", type=click.STRING, default="img")
@click.option("--dst", "-d", type=click.STRING, default="")
@click.pass_context
def resize(
    ctx: click.Context, width: int, height: int, src: str, dst: str, algorithm: str
):
    """Resizes image to a specific width/height."""
    transformer: Transformer = ctx.obj
    transformer.resize(src, dst, width, height, algorithm)


@cli.command()
@click.option("--width", "-w", type=click.IntRange(min=-1), default=-1)
@click.option("--height", "-h", type=click.IntRange(min=-1), default=-1)
@click.option(
    "--pivot-x", "-px", type=click.FloatRange(min=0, max=1, clamp=True), default=0.5
)
@click.option(
    "--pivot-y", "-py", type=click.FloatRange(min=0, max=1, clamp=True), default=0.5
)
@click.option("--color", "-c", type=click.STRING, default="FFF0")
@click.option("--src", "-s", type=click.STRING, default="img")
@click.option("--dst", "-d", type=click.STRING, default="")
@click.pass_context
def pad(
    ctx: click.Context,
    width: int,
    height: int,
    pivot_x: float,
    pivot_y: float,
    color: str,
    src: str,
    dst: str,
):
    """Pads pixels around the image."""
    transformer: Transformer = ctx.obj
    transformer.pad(src, dst, width, height, pivot_x, pivot_y, color)


@cli.command()
@click.option("--color", "-c", type=click.STRING, default="FFF")
@click.option("--src", "-s", type=click.STRING, default="img")
@click.option("--dst", "-d", type=click.STRING, default="")
@click.pass_context
def extract_alpha(ctx: click.Context, color: str, src: str, dst: str):
    """Extract the alpha channel with a new color."""
    transformer: Transformer = ctx.obj
    transformer.extract_alpha(src, dst, color)


@cli.command()
@click.option("--radius", "-r", type=click.IntRange(min=1), default=1)
@click.option("--src", "-s", type=click.STRING, default="img")
@click.option("--dst", "-d", type=click.STRING, default="")
@click.pass_context
def dilate(ctx: click.Context, radius: int, src: str, dst: str):
    """Dilates the image by radius."""
    transformer: Transformer = ctx.obj
    transformer.dilate(src, dst, radius)


@cli.command()
@click.option("--radius", "-r", type=click.IntRange(min=1), default=1)
@click.option("--src", "-s", type=click.STRING, default="img")
@click.option("--dst", "-d", type=click.STRING, default="")
@click.pass_context
def erode(ctx: click.Context, radius: int, src: str, dst: str):
    """Erodes the image by radius."""
    transformer: Transformer = ctx.obj
    transformer.erode(src, dst, radius)


@cli.command()
@click.option("--radius", "-r", type=click.IntRange(min=1), default=1)
@click.option("--src", "-s", type=click.STRING, default="img")
@click.option("--dst", "-d", type=click.STRING, default="")
@click.pass_context
def blur(ctx: click.Context, radius: int, src: str, dst: str):
    """Gaussian blurs the image by radius."""
    transformer: Transformer = ctx.obj
    transformer.blur(src, dst, radius)


@cli.command()
@click.option("--channel", "-c", type=click.IntRange(min=0, max=3), default=3)
@click.option("--src", "-s", type=click.STRING, default="img")
@click.option("--by", "-b", type=click.STRING, default="img")
@click.option("--dst", "-d", type=click.STRING, default="")
@click.pass_context
def subtract(ctx: click.Context, channel: int, src: str, by: str, dst: str):
    """Subtracts one image from the other."""
    transformer: Transformer = ctx.obj
    transformer.subtract(src, by, dst, channel)
