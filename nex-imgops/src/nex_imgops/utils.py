import numpy as np

COLOR_TABLE = {
    "indianred": "cd5c5c",
    "lightcoral": "f08080",
    "salmon": "fa8072",
    "darksalmon": "e9967a",
    "lightsalmon": "ffa07a",
    "crimson": "dc143c",
    "red": "ff0000",
    "firebrick": "b22222",
    "darkred": "8b0000",
    "pink": "ffc0cb",
    "lightpink": "ffb6c1",
    "hotpink": "ff69b4",
    "deeppink": "ff1493",
    "mediumvioletred": "c71585",
    "palevioletred": "db7093",
    "coral": "ff7f50",
    "tomato": "ff6347",
    "orangered": "ff4500",
    "darkorange": "ff8c00",
    "orange": "ffa500",
    "gold": "ffd700",
    "yellow": "ffff00",
    "lightyellow": "ffffe0",
    "lemonchiffon": "fffacd",
    "lightgoldenrodyellow": "fafad2",
    "papayawhip": "ffefd5",
    "moccasin": "ffe4b5",
    "peachpuff": "ffdab9",
    "palegoldenrod": "eee8aa",
    "khaki": "f0e68c",
    "darkkhaki": "bdb76b",
    "lavender": "e6e6fa",
    "thistle": "d8bfd8",
    "plum": "dda0dd",
    "violet": "ee82ee",
    "orchid": "da70d6",
    "fuchsia": "ff00ff",
    "magenta": "ff00ff",
    "mediumorchid": "ba55d3",
    "mediumpurple": "9370db",
    "blueviolet": "8a2be2",
    "darkviolet": "9400d3",
    "darkorchid": "9932cc",
    "darkmagenta": "8b008b",
    "purple": "800080",
    "rebeccapurple": "663399",
    "indigo": "4b0082",
    "mediumslateblue": "7b68ee",
    "slateblue": "6a5acd",
    "darkslateblue": "483d8b",
    "greenyellow": "adff2f",
    "chartreuse": "7fff00",
    "lawngreen": "7cfc00",
    "lime": "00ff00",
    "limegreen": "32cd32",
    "palegreen": "98fb98",
    "lightgreen": "90ee90",
    "mediumspringgreen": "00fa9a",
    "springgreen": "00ff7f",
    "mediumseagreen": "3cb371",
    "seagreen": "2e8b57",
    "forestgreen": "228b22",
    "green": "008000",
    "darkgreen": "006400",
    "yellowgreen": "9acd32",
    "olivedrab": "6b8e23",
    "olive": "808000",
    "darkolivegreen": "556b2f",
    "mediumaquamarine": "66cdaa",
    "darkseagreen": "8fbc8f",
    "lightseagreen": "20b2aa",
    "darkcyan": "008b8b",
    "teal": "008080",
    "aqua": "00ffff",
    "cyan": "00ffff",
    "lightcyan": "e0ffff",
    "paleturquoise": "afeeee",
    "aquamarine": "7fffd4",
    "turquoise": "40e0d0",
    "mediumturquoise": "48d1cc",
    "darkturquoise": "00ced1",
    "cadetblue": "5f9ea0",
    "steelblue": "4682b4",
    "lightsteelblue": "b0c4de",
    "powderblue": "b0e0e6",
    "lightblue": "add8e6",
    "skyblue": "87ceeb",
    "lightskyblue": "87cefa",
    "deepskyblue": "00bfff",
    "dodgerblue": "1e90ff",
    "cornflowerblue": "6495ed",
    "royalblue": "4169e1",
    "blue": "0000ff",
    "mediumblue": "0000cd",
    "darkblue": "00008b",
    "navy": "000080",
    "midnightblue": "191970",
    "cornsilk": "fff8dc",
    "blanchedalmond": "ffebcd",
    "bisque": "ffe4c4",
    "navajowhite": "ffdead",
    "wheat": "f5deb3",
    "burlywood": "deb887",
    "tan": "d2b48c",
    "rosybrown": "bc8f8f",
    "sandybrown": "f4a460",
    "goldenrod": "daa520",
    "darkgoldenrod": "b8860b",
    "peru": "cd853f",
    "chocolate": "d2691e",
    "saddlebrown": "8b4513",
    "sienna": "a0522d",
    "brown": "a52a2a",
    "maroon": "800000",
    "white": "ffffff",
    "snow": "fffafa",
    "honeydew": "f0fff0",
    "mintcream": "f5fffa",
    "azure": "f0ffff",
    "aliceblue": "f0f8ff",
    "ghostwhite": "f8f8ff",
    "whitesmoke": "f5f5f5",
    "seashell": "fff5ee",
    "beige": "f5f5dc",
    "oldlace": "fdf5e6",
    "floralwhite": "fffaf0",
    "ivory": "fffff0",
    "antiquewhite": "faebd7",
    "linen": "faf0e6",
    "lavenderblush": "fff0f5",
    "mistyrose": "ffe4e1",
    "gainsboro": "dcdcdc",
    "lightgray": "d3d3d3",
    "lightgrey": "d3d3d3",
    "silver": "c0c0c0",
    "darkgray": "a9a9a9",
    "darkgrey": "a9a9a9",
    "gray": "808080",
    "grey": "808080",
    "dimgray": "696969",
    "dimgrey": "696969",
    "lightslategray": "778899",
    "lightslategrey": "778899",
    "slategray": "708090",
    "slategrey": "708090",
    "darkslategray": "2f4f4f",
    "darkslategrey": "2f4f4f",
    "black": "000000",
}


def _parse_hex(code: str) -> int:
    return int(code, 16)


def _parse_color3(code: str) -> np.array:
    l = len(code)
    if l == 0:
        code = "000"
    elif l < 3:
        code = code * 3
    elif l < 6:
        code = code[
            :3
        ]  # For 4, it means dropping the alpha. For 5... It's probably garbage.
    elif l > 6:
        code = code[:6]

    # We have len(code) % 3 == 0
    if len(code) == 3:
        return np.array(
            [
                17 * _parse_hex(code[0]),
                17 * _parse_hex(code[1]),
                17 * _parse_hex(code[2]),
            ],
            dtype=np.uint8,
        ).reshape((1, 1, 3))
    else:
        return np.array(
            [_parse_hex(code[0:2]), _parse_hex(code[2:4]), _parse_hex(code[4:6])],
            dtype=np.uint8,
        ).reshape((1, 1, 3))


def _parse_color4(code: str) -> np.array:
    l = len(code)
    if l == 0:
        code = "000F"
    if l == 1:
        code = code * 3 + "F"
    elif l == 2:
        code = code * 4 + "F"
    elif l == 3:
        code = code + "F"
    elif l == 5:
        code = code[0:4]
    elif l == 6:
        code = code + "FF"
    elif l == 7:
        code = code + code[-1]
    elif l > 8:
        code = code[0:8]
    # We have len(code) % 4 == 0
    if len(code) == 4:
        return np.array(
            [
                17 * _parse_hex(code[0]),
                17 * _parse_hex(code[1]),
                17 * _parse_hex(code[2]),
                17 * _parse_hex(code[3]),
            ],
            dtype=np.uint8,
        ).reshape((1, 1, 4))
    else:
        return np.array(
            [
                _parse_hex(code[0:2]),
                _parse_hex(code[2:4]),
                _parse_hex(code[4:6]),
                _parse_hex(code[6:8]),
            ],
            dtype=np.uint8,
        ).reshape((1, 1, 4))


def parse_color3(name: str) -> np.array:
    if name.startswith("#"):
        return _parse_color3(name[1:])
    elif name in COLOR_TABLE:
        return _parse_color3(COLOR_TABLE[name])
    else:
        return _parse_color3(name)


def parse_color4(name: str) -> np.array:
    if name.startswith("#"):
        return _parse_color4(name[1:])
    elif name in COLOR_TABLE:
        return _parse_color4(COLOR_TABLE[name])
    else:
        return _parse_color4(name)


def create_single_white_pixel() -> np.array:
    return np.array([255, 255, 255, 255], dtype=np.uint8).reshape((1, 1, 4))


def create_filled_rect(width: int, height: int, color: np.array) -> np.array:
    ret = np.zeros((height, width, 4), dtype=np.uint8)
    ret[:, :, :] = color
    return ret
