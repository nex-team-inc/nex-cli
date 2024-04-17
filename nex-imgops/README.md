# Nex Image Operations

## Overview

`nex-imgops` is a library that provides image modification utilities. It reads any image as a RGBA pixel buffer and perform various image operations before saving it. It is similar to ffmpeg in that it is also a streamline transformer. This is supposed to use in conjunction with the `nex` command.

## Usage

For help, type:

```bash
nex imgops --help
```

It always starts with an image source (default to a 1x1 all white pixel) with

```bash
nex imgops --input "source.png" save "output.png"
```

The save command will save the image buffer into the specified file.
