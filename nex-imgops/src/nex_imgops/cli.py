from typing import Any, Optional, Dict, Callable
from .transformer import Transformer
from functools import wraps

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


class AliasedGroup(click.Group):
    def __init__(self, *kargs, alias_map: Dict[str, str], **kwargs) -> None:
        super().__init__(*kargs, **kwargs)
        self._alias_map = alias_map

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        cmd_name = self._alias_map.get(
            cmd_name, cmd_name
        )  # Try to see if there is already a defined lookup.
        return super().get_command(ctx, cmd_name)


@click.group(cls=AliasedGroup, chain=True, alias_map={"extract-alpha": "alpha"})
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


def transformer_adaptor(func: Callable):
    def decorator(f: Callable):
        @click.pass_context
        @wraps(func)
        def wrapped(ctx: click.Context, *args, **kwargs):
            transformer: Transformer = ctx.obj
            func(transformer, *args, **kwargs)

        return wrapped

    return decorator


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@_dst_option
@transformer_adaptor(Transformer.load)
def load():
    pass


@cli.command(name="filled")
@_dst_option
@click.option("--width", "-w", type=click.IntRange(min=1), default=1)
@click.option("--height", "-h", type=click.IntRange(min=1), default=1)
@click.option(
    "--color",
    "-c",
    type=click.STRING,
    default="FFFF",
    help="Base color of the filled rect.",
)
@transformer_adaptor(Transformer.filled_rect)
def filled():
    pass


@cli.command()
@click.argument("path", type=click.Path())
@_src_option
@transformer_adaptor(Transformer.save)
def save():
    pass


@cli.command()
@_src_option
@_dst_option
@transformer_adaptor(Transformer.clone)
def clone():
    pass


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
@transformer_adaptor(Transformer.resize)
def resize():
    pass


@cli.command()
@_src_option
@_dst_option
@click.option("--width", "-w", type=int, default=0)
@click.option("--height", "-h", type=int, default=0)
@click.option(
    "--pivot-x",
    "-px",
    "px",
    type=click.FloatRange(min=0, max=1, clamp=True),
    default=0.5,
)
@click.option(
    "--pivot-y",
    "-py",
    "py",
    type=click.FloatRange(min=0, max=1, clamp=True),
    default=0.5,
)
@click.option("--color", "-c", type=click.STRING, default="FFF0")
@transformer_adaptor(Transformer.pad)
def pad():
    pass


@cli.command("alpha")
@_src_option
@_dst_option
@click.option(
    "--color", "-c", type=click.STRING, default="FFF", help="RGB for non-alpha channel."
)
@transformer_adaptor(Transformer.extract_alpha)
def extract_alpha():
    pass


@cli.command()
@_src_option
@_dst_option
@click.option(
    "--radius", "-r", type=click.IntRange(min=1), default=1, help="Radius for dilation"
)
@transformer_adaptor(Transformer.dilate)
def dilate():
    pass


@cli.command()
@_src_option
@_dst_option
@click.option(
    "--radius", "-r", type=click.IntRange(min=1), default=1, help="Radius for erosion"
)
@transformer_adaptor(Transformer.erode)
def erode():
    pass


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
@transformer_adaptor(Transformer.blur)
def blur():
    pass


@cli.command(name="rounded")
@_src_option
@_dst_option
@click.option(
    "--top-left",
    "-tl",
    "tl",
    type=click.FloatRange(min=0),
    default=1,
    help="Top Left Radius",
)
@click.option(
    "--top-right",
    "-tr",
    "tr",
    type=click.FloatRange(min=0),
    default=1,
    help="Top Right Radius",
)
@click.option(
    "--bottom-left",
    "-bl",
    "bl",
    type=click.FloatRange(min=0),
    default=1,
    help="Bottom Left Radius",
)
@click.option(
    "--bottom-right",
    "-br",
    "br",
    type=click.FloatRange(min=0),
    default=1,
    help="Bottom Right Radius",
)
@click.option(
    "--base-radius",
    "-b",
    "base",
    type=click.FloatRange(min=0),
    default=1,
    help="The base radius, so that we can tune all 4 radius together.",
)
@click.option(
    "--stroke",
    "-s",
    "stroke",
    type=click.FloatRange(min=0, min_open=True),
    default=None,
    help="Stroke Border Width",
)
@click.option(
    "--weight",
    "-w",
    "weight",
    type=click.FloatRange(min=0),
    default=1,
    help="The relative weight between Width / Height if scale mode is relative.",
)
@click.option(
    "--scale-mode",
    "-m",
    "scale_mode",
    default="const",
    type=click.Choice(("const", "rel"), case_sensitive=False),
)
@click.option(
    "--falloff",
    "-f",
    "falloff",
    type=click.FloatRange(min=0),
    default=0,
    help="The falloff fade-out.",
)
@transformer_adaptor(Transformer.apply_rounded_corners)
def apply_rounded_corners():
    pass


@cli.command()
@_src_option
@_dst_option
@click.option("--color", "-c", type=click.STRING, default="FFFF", help="Tint color")
@transformer_adaptor(Transformer.tint)
def tint():
    pass


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
@transformer_adaptor(Transformer.subtract)
def subtract():
    pass


@cli.command()
@_src_option
@_dst_option
@click.option(
    "--by", "-b", type=click.STRING, default=None, help="The multiplying matrix."
)
@transformer_adaptor(Transformer.multiply)
def multiply():
    pass


@cli.command()
@_src_option
@_dst_option
@click.option(
    "--horizontal", "-h", is_flag=True, default=False, help="Flip horizontally."
)
@click.option("--vertical", "-v", is_flag=True, default=False, help="Flip vertically.")
@transformer_adaptor(Transformer.flip)
def flip():
    pass


@cli.command()
@_src_option
@_dst_option
@click.pass_context
def vflip(ctx: click.Context, src: Optional[str] = None, dst: Optional[str] = None):
    ctx.invoke(flip, src=src, dst=dst, horizontal=False, vertical=True)


@cli.command()
@_src_option
@_dst_option
@click.pass_context
def hflip(ctx: click.Context, src: Optional[str] = None, dst: Optional[str] = None):
    ctx.invoke(flip, src=src, dst=dst, horizontal=True, vertical=False)


@cli.command()
@_src_option
@_dst_option
@click.option("--left", "-l", count=True)
@click.option("--right", "-r", count=True)
@transformer_adaptor(Transformer.rotate)
def rotate():
    pass
