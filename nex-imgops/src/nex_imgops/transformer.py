from typing import Dict, Optional
import numpy as np
from . import ops


class Transformer:
    DEFAULT_SRC = "img"

    def __init__(self) -> None:
        self._context: Dict[str, np.array] = {}

    def load(self, path: str, dst: str) -> None:
        if dst == "":
            dst = self.DEFAULT_SRC
        self._context[dst] = ops.load(path)

    def save(self, path: str, src: str) -> None:
        ops.save(self._context[src], path)

    def clone(self, src: str, dst: str) -> None:
        if dst == "":
            dst = src
        if dst != src:
            self._context[dst] = ops.clone(self._context[src])

    def resize(
        self, src: str, dst: str, width: int, height: int, algorithm: str
    ) -> None:
        if dst == "":
            dst = src
        self._context[dst] = ops.resize(self._context[src], width, height, algorithm)

    def pad(
        self,
        src: str,
        dst: str,
        width: int = 0,
        height: int = 0,
        px: float = 0.5,
        py: float = 0.5,
        color: str = "0000",
    ) -> None:
        if dst == "":
            dst = src
        self._context[dst] = ops.pad(self._context[src], width, height, px, py, color)

    def extract_alpha(self, src: str, dst: str, color: str = "FFF") -> None:
        if dst == "":
            dst = src
        self._context[dst] = ops.extract_alpha(
            self._context[src], color, in_place=src == dst
        )

    def dilate(self, src: str, dst: str, radius: int) -> None:
        if dst == "":
            dst = src
        self._context[dst] = ops.dilate(self._context[src], radius)

    def erode(self, src: str, dst: str, radius: int) -> None:
        if dst == "":
            dst = src
        self._context[dst] = ops.erode(self._context[src], radius)

    def blur(self, src: str, dst: str, radius: int) -> None:
        if dst == "":
            dst = src
        self._context[dst] = ops.blur(self._context[src], radius)

    def subtract(self, src: str, by: str, dst: str, channel: int) -> None:
        if dst == "":
            dst = src
        self._context[dst] = ops.subtract(
            self._context[src], self._context[by], channel, src == dst
        )
