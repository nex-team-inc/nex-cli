import click
import cv2
import numpy as np
import os.path
from PIL import Image
from typing import Optional

from .utils import parse_color3, parse_color4, create_single_white_pixel


def load(path: Optional[str]) -> np.array:
    if path is None or path == "" or not os.path.isfile(path):
        return create_single_white_pixel()

    try:
        with Image.open(path) as raw_image:
            source = raw_image
            if raw_image.mode != "RGBA":
                source = raw_image.convert("RGBA")
            return np.array(source)
    except Exception as ex:
        click.echo(f"Error reading image file {path}")
        click.echo(ex)
        return create_single_white_pixel()


def save(img: np.array, path: str) -> None:
    Image.fromarray(img, mode="RGBA").save(path)


def clone(img: np.array) -> np.array:
    return img.copy()


def resize(
    img: np.array, width: int = -1, height: int = -1, algorithm: str = "auto"
) -> np.array:
    (fh, fw, _) = img.shape
    if width == -1:
        if height == -1:
            th = fh
            tw = fw
            is_shrinking = False
        else:
            th = height
            tw = (2 * fw * th + fh) // (2 * fh)
            is_shrinking = fh > th
    else:
        if height == -1:
            tw = width
            th = (2 * fh * tw + fw) // (2 * fw)
            is_shrinking = fw > tw
        else:
            tw = width
            th = height
            is_shrinking = fw * fh > tw * th

    algorithm = algorithm.lower()
    if algorithm == "linear":
        interpolation = cv2.INTER_LINEAR
    elif algorithm == "cubic":
        interpolation = cv2.INTER_CUBIC
    elif algorithm == "nearest":
        interpolation = cv2.INTER_NEAREST
    elif algorithm == "area":
        interpolation = cv2.INTER_AREA
    else:
        interpolation = cv2.INTER_AREA if is_shrinking else cv2.INTER_CUBIC
    return cv2.resize(img, (tw, th), interpolation=interpolation)


def pad(
    img: np.array,
    width: int = 0,
    height: int = 0,
    px: float = 0.5,
    py: float = 0.5,
    color: str = "0000",
):
    left = round(width * px)
    right = width - left
    top = round(height * py)
    bottom = height - top
    (fh, fw, _) = img.shape
    ret = np.zeros((fh + height, fw + height, 4), dtype=np.uint8)
    ret[:, :, :] = parse_color4(color)
    ret[top:-bottom, left:-right:, :] = img
    return ret


def extract_alpha(
    img: np.array, color: str = "FFF", in_place: bool = False
) -> np.array:
    rgb = parse_color3(color)
    if in_place:
        ret = img
    else:
        (height, width, _) = img.shape
        ret = np.zeros((height, width, 4), dtype=np.uint8)
        ret[:, :, 3] = img[:, :, 3]

    ret[:, :, 0:3] = rgb
    return ret


def dilate(img: np.array, radius: int) -> np.array:
    structure_size = 2 * radius + 1
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (structure_size, structure_size)
    )
    return cv2.dilate(img, kernel)


def erode(img: np.array, radius: int) -> np.array:
    structure_size = 2 * radius + 1
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (structure_size, structure_size)
    )
    return cv2.erode(img, kernel)


def blur(img: np.array, radius: int) -> np.array:
    kernel_size = 2 * radius + 1
    sigma = radius * 0.5
    return cv2.GaussianBlur(img, (kernel_size, kernel_size), sigmaX=sigma, sigmaY=sigma)


def subtract(
    src: np.array, by: np.array, channel: int = 3, in_place: bool = False
) -> np.array:
    if in_place:
        ret = src
    else:
        ret = src.copy()
    ret[:, :, channel] -= by[:, :, channel]
    return ret
