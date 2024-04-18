import functools
from typing import Dict, Optional
import numpy as np
from . import ops


def _with_default_str(value: Optional[str], default_value: str) -> str:
    return default_value if value is None or value == "" else value


def _with_default_int(value: Optional[int], default_value: int) -> int:
    return default_value if value is None else value


def _with_default_float(value: Optional[float], default_value: float) -> float:
    return default_value if value is None else value


class Transformer:
    DEFAULT_SRC = "img"
    DEFAULT_OUTPUT_PATH = "out.png"

    def __init__(
        self, initial_name: str = DEFAULT_SRC, path: Optional[str] = None
    ) -> None:
        self._context: Dict[str, np.array] = {}
        self._curr = initial_name
        self._dst = self._curr
        self._context[self._curr] = ops.load(path)

    def wrap_src_dst(func):
        @functools.wraps(func)
        def inner(
            self: "Transformer",
            *kargs,
            src: Optional[str] = None,
            dst: Optional[str] = None,
            **kwargs
        ):
            src = _with_default_str(src, self._curr)
            dst = _with_default_str(dst, src)
            func(self, src=src, dst=dst, *kargs, **kwargs)
            self._curr = dst
            return self._curr

        return inner

    def load(self, dst: Optional[str] = None, path: Optional[str] = None) -> str:
        self._curr = _with_default_str(dst, self._curr)
        self._context[self._curr] = ops.load(path)
        return self._curr

    def save(self, src: Optional[str] = None, path: Optional[str] = None) -> str:
        self._curr = _with_default_str(src, self._curr)
        ops.save(
            self._context[self._curr], _with_default_str(path, self.DEFAULT_OUTPUT_PATH)
        )
        return self._curr

    @wrap_src_dst
    def clone(self, src: str, dst: str) -> None:
        if dst != src:
            self._context[dst] = ops.clone(self._context[src])

    @wrap_src_dst
    def resize(
        self,
        src: str,
        dst: str,
        width: Optional[int] = -1,
        height: Optional[int] = -1,
        algorithm: Optional[str] = "auto",
    ) -> None:
        self._context[dst] = ops.resize(
            self._context[src], width, height, _with_default_str(algorithm, "auto")
        )

    @wrap_src_dst
    def pad(
        self,
        src: str,
        dst: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        px: Optional[float] = None,
        py: Optional[float] = None,
        color: Optional[str] = None,
    ) -> None:
        self._context[dst] = ops.pad(
            self._context[src],
            _with_default_int(width, 0),
            _with_default_int(height, 0),
            _with_default_float(px, 0.5),
            _with_default_float(py, 0.5),
            _with_default_str(color, "0000"),
        )

    @wrap_src_dst
    def extract_alpha(self, src: str, dst: str, color: Optional[str] = None) -> None:
        self._context[dst] = ops.extract_alpha(
            self._context[src], _with_default_str(color, "FFF"), in_place=src == dst
        )

    @wrap_src_dst
    def dilate(self, src: str, dst: str, radius: Optional[int] = None) -> None:
        self._context[dst] = ops.dilate(
            self._context[src], _with_default_int(radius, 1)
        )

    @wrap_src_dst
    def erode(self, src: str, dst: str, radius: Optional[int] = None) -> None:
        self._context[dst] = ops.erode(self._context[src], _with_default_int(radius, 1))

    @wrap_src_dst
    def blur(self, src: str, dst: str, radius: Optional[int] = None) -> None:
        self._context[dst] = ops.blur(self._context[src], _with_default_int(radius, 1))

    @wrap_src_dst
    def subtract(
        self,
        src: str,
        dst: str,
        by: Optional[str] = None,
        channel: Optional[int] = None,
    ) -> None:
        by = _with_default_str(by, src)
        self._context[dst] = ops.subtract(
            self._context[src],
            self._context[by],
            _with_default_int(channel, 3),
            src == dst,
        )
