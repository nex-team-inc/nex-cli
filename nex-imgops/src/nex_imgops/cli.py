from typing import Optional
from .transformer import Transformer

import click

_src_option = click.option(
    "--src",
    "-s",
    type=click.STRING,
    default=None,
    help="Specify the source image id",
)
_dst_option = click.option(
    "--dst",
    "-d",
    type=click.STRING,
    default=None,
    help="Specify the destination image id",
)


@click.group(chain=True)
@_dst_option
@click.option(
    "--input",
    "-i",
    type=click.Path(exists=True),
    default=None,
    help="Specify the initial image path.",
)
@click.pass_context
def cli(
    ctx: click.Context, dst: Optional[str] = None, input: Optional[str] = None
) -> None:
    """Transform images using subcommands."""
    ctx.ensure_object(Transformer)
    transformer: Transformer = ctx.obj
    transformer.load(dst=dst, path=input)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@_dst_option
@click.pass_context
def load(ctx: click.Context, path: str, dst: Optional[str] = None) -> None:
    """Load an image to dst."""
    transformer: Transformer = ctx.obj
    transformer.load(dst=dst, path=path)


@cli.command()
@click.argument("path", type=click.Path())
@_src_option
@click.pass_context
def save(ctx: click.Context, path: str, src: Optional[str] = None):
    """Save an image from src to a file."""
    transformer: Transformer = ctx.obj
    transformer.save(src=src, path=path)


@cli.command()
@_src_option
@_dst_option
@click.pass_context
def clone(ctx: click.Context, src: Optional[str] = None, dst: Optional[str] = None):
    """Clone an image from src to dst."""
    transformer: Transformer = ctx.obj
    transformer.clone(src=src, dst=dst)


@cli.command()
@_src_option
@_dst_option
@click.option(
    "--width",
    "-w",
    type=click.IntRange(min=-1),
    default=-1,
    help="Target width after resize.",
)
@click.option(
    "--height",
    "-h",
    type=click.IntRange(min=-1),
    default=-1,
    help="Target height after resize.",
)
@click.option(
    "--algorithm",
    "-a",
    type=click.Choice(
        ("auto", "linear", "nearest", "cubic", "area"), case_sensitive=False
    ),
    default="auto",
)
@click.pass_context
def resize(
    ctx: click.Context,
    src: Optional[str] = None,
    dst: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    algorithm: Optional[str] = None,
):
    """Resizes image to a specific width/height."""
    transformer: Transformer = ctx.obj
    transformer.resize(
        src=src, dst=dst, width=width, height=height, algorithm=algorithm
    )


@cli.command()
@_src_option
@_dst_option
@click.option("--width", "-w", type=click.IntRange(min=-1), default=-1)
@click.option("--height", "-h", type=click.IntRange(min=-1), default=-1)
@click.option(
    "--pivot-x", "-px", type=click.FloatRange(min=0, max=1, clamp=True), default=0.5
)
@click.option(
    "--pivot-y", "-py", type=click.FloatRange(min=0, max=1, clamp=True), default=0.5
)
@click.option("--color", "-c", type=click.STRING, default="FFF0")
@click.pass_context
def pad(
    ctx: click.Context,
    src: Optional[str] = None,
    dst: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    pivot_x: Optional[float] = None,
    pivot_y: Optional[float] = None,
    color: Optional[str] = None,
):
    """Pads pixels around the image."""
    transformer: Transformer = ctx.obj
    transformer.pad(
        src=src,
        dst=dst,
        width=width,
        height=height,
        px=pivot_x,
        py=pivot_y,
        color=color,
    )


@cli.command()
@_src_option
@_dst_option
@click.option(
    "--color", "-c", type=click.STRING, default="FFF", help="RGB for non-alpha channel."
)
@click.pass_context
def extract_alpha(
    ctx: click.Context,
    src: Optional[str] = None,
    dst: Optional[str] = None,
    color: Optional[str] = None,
):
    """Extract the alpha channel with a new color."""
    transformer: Transformer = ctx.obj
    transformer.extract_alpha(src=src, dst=dst, color=color)


@cli.command()
@_src_option
@_dst_option
@click.option(
    "--radius", "-r", type=click.IntRange(min=1), default=1, help="Radius for dilation"
)
@click.pass_context
def dilate(
    ctx: click.Context,
    src: Optional[str] = None,
    dst: Optional[str] = None,
    radius: Optional[int] = None,
):
    """Dilates the image by radius."""
    transformer: Transformer = ctx.obj
    transformer.dilate(src=src, dst=dst, radius=radius)


@cli.command()
@_src_option
@_dst_option
@click.option(
    "--radius", "-r", type=click.IntRange(min=1), default=1, help="Radius for erosion"
)
@click.pass_context
def erode(
    ctx: click.Context,
    src: Optional[str] = None,
    dst: Optional[str] = None,
    radius: Optional[int] = None,
):
    """Erodes the image by radius."""
    transformer: Transformer = ctx.obj
    transformer.erode(src=src, dst=dst, radius=radius)


@cli.command()
@_src_option
@_dst_option
@click.option(
    "--radius",
    "-r",
    type=click.IntRange(min=1),
    default=1,
    help="Radius for Gaussian blur",
)
@click.pass_context
def blur(
    ctx: click.Context,
    src: Optional[str] = None,
    dst: Optional[str] = None,
    radius: Optional[int] = None,
):
    """Gaussian blurs the image by radius."""
    transformer: Transformer = ctx.obj
    transformer.blur(src=src, dst=dst, radius=radius)


@cli.command()
@_src_option
@_dst_option
@click.option(
    "--by", "-b", type=click.STRING, default=None, help="The Subtrahend data."
)
@click.option(
    "--channel",
    "-c",
    type=click.IntRange(min=0, max=3),
    default=3,
    help="The channel subtraction happens.",
)
@click.pass_context
def subtract(
    ctx: click.Context,
    src: Optional[str] = None,
    dst: Optional[str] = None,
    channel: Optional[int] = None,
    by: Optional[str] = None,
):
    """Subtracts one image from the other."""
    transformer: Transformer = ctx.obj
    transformer.subtract(src=src, dst=dst, by=by, channel=channel)
