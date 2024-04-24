import click
import cv2
import numpy as np
import os.path
from PIL import Image
from typing import Optional

from .utils import (
    parse_color3,
    parse_color4,
    create_single_white_pixel,
    create_filled_rect,
)


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


def filled_rect(width: int, height: int, color: np.array) -> np.array:
    return create_filled_rect(width, height, parse_color4(color))


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
    (sh, sw, _) = img.shape
    dh = sh + height
    dw = sw + width
    ret = np.zeros((dh, dw, 4), dtype=np.uint8)
    ret[:, :, :] = parse_color4(color)
    dst_y_begin = max(top, 0)
    dst_y_end = min(dh - bottom, dh)
    dst_x_begin = max(left, 0)
    dst_x_end = min(dw - right, dw)
    src_y_begin = max(0, -top)
    src_y_end = min(sh + bottom, sh)
    src_x_begin = max(0, -left)
    src_x_end = min(sw + right, sw)
    ret[dst_y_begin:dst_y_end, dst_x_begin:dst_x_end:, :] = img[
        src_y_begin:src_y_end, src_x_begin:src_x_end, :
    ]
    return ret


def _clone_if_not_in_place(img: np.array, in_place: bool = False) -> np.array:
    return img if in_place else img.copy()


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


def apply_rounded_corners(
    img: np.array,
    tl: float,
    tr: float,
    bl: float,
    br: float,
    stroke: float,
    falloff: float,
    in_place: bool = False,
) -> np.array:
    ret = _clone_if_not_in_place(img, in_place)
    (height, width, _) = ret.shape

    # For uniformity, we treat each pixel to be centered at its center, so at 0.5 coordinates.
    # As a result, the edges of the (0, 0) pixel are from (-0.5 -> 0.5) in both x and y direction.
    # The radius are also defined similarly. They are the distance from the edge to the center.
    # However, to make things more semmetric, we will keep them all positive, in their principle location,
    # but rotate our point around the corners to keep things "standardized".
    # What that means is that we want to pretend the radius center is at the origin, and the point is (x', y')
    # to the right, top direction of it.
    radii = np.array(((tl, bl, br, tr),), dtype=np.float32)
    # If we know the edges the origin anchors to, we can compute x', y' very easily. For example, for TL, the anchors
    # are the left and top edge. (x', y') are essentially (tl - (x + 0.5), tl - (y + 0.5)).
    # For each corner, the anchors are different, and we need a configuration for that.
    # The following scales matrix tells us where each point is anchored from.
    # If the scale -1, it means it is anchoring from left / top edge. If the scale is 1, it means it is anchoring from
    # right / bottom edge.
    scales = np.array(
        (
            (-1, -1, 1, 1),
            (-1, 1, 1, -1),
        ),
        dtype=np.float32,
    )
    dimensions = np.array(
        (
            (width,),
            (height,),
        ),
        dtype=np.float32,
    )
    # To get the respective distance from the edge, we can simply use
    # dimensions * (scales + 1) * 0.5 - scales * (x, y)

    pt = np.zeros((2, 1), dtype=np.float32)

    neg_inf = np.array(((-1.5 * max(width, height),),), dtype=np.float32)

    # We have the 4 centers.
    for y in range(height):
        for x in range(width):
            # For each point, we want to know how it compares with the 4 centers, and how much it is from the edge.
            xx = pt[0, 0] = x + 0.5
            yy = pt[1, 0] = y + 0.5
            bound_dists = np.array(
                (-xx, yy - height, xx - width, -yy), dtype=np.float32
            )
            std_xy = dimensions * (scales + 1) * 0.5 - scales * pt
            std_dxy = radii - std_xy
            corner_dists = np.linalg.norm(std_dxy, axis=0) - radii
            valid_corners = np.logical_and(std_dxy[0, :] >= 0, std_dxy[1, :] >= 0)

            outer_dist = max(
                bound_dists.max(), np.where(valid_corners, corner_dists, neg_inf).max()
            )

            inner_dist = max(
                bound_dists.max() + stroke,
                np.where(valid_corners, corner_dists + stroke, neg_inf).max(),
            )

            # At this point, outer_dist > 0 means outside. inner_dist < 0 means too-inside.
            # As a result, if we want to mark the "good" region as positive, we should use -outer_dist and inner_dist.
            # We compute signed_dist, which is basically the distance from the closest border, with negative meaning
            # in the clipped region.
            signed_dist = min(-outer_dist, inner_dist)

            if signed_dist < 0:
                ret[y, x, 3] = 0
            elif falloff > 1e-8 and signed_dist < falloff:
                ret[y, x, 3] *= signed_dist / falloff

    return ret


def tint(src: np.array, color: str, in_place: bool = False) -> np.array:
    ret = _clone_if_not_in_place(src, in_place)
    color4 = parse_color4(color)
    cv2.multiply(src, color4.reshape((4,)), ret, scale=1 / 255)
    return ret


def subtract(
    src: np.array, by: np.array, channel: int = 3, in_place: bool = False
) -> np.array:
    ret = _clone_if_not_in_place(src, in_place)
    ret[:, :, channel] -= by[:, :, channel]
    return ret


def multiply(src: np.array, by: np.array, in_place: bool = False) -> np.array:
    ret = _clone_if_not_in_place(src, in_place)
    cv2.multiply(src, by, ret, scale=1 / 255)
    return ret


def flip(
    src: np.array, horizontal: bool, vertical: bool, in_place: bool = False
) -> np.array:
    if horizontal:
        if vertical:
            return np.flip(src, (0, 1))
        else:
            return np.flip(src, 1)
    else:
        if vertical:
            return np.flip(src, 0)
        else:
            return src if in_place else src.copy()


def rotate(src: np.array, ccw: int, in_place: bool) -> np.array:
    """Rotate the src image by ccw times ccw."""
    ccw %= 4  # This is either 0, 1, 2, 3
    if ccw == 0:
        return src if in_place else src.copy()
    else:
        return np.rot90(src, ccw, axes=(0, 1))
