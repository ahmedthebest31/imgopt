# imgopt-cli

[![PyPI version](https://badge.fury.io/py/imgopt-cli.svg)](https://badge.fury.io/py/imgopt-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/imgopt-cli.svg)](https://pypi.org/project/imgopt-cli/)

**The Intelligent WebP Converter for Modern Web Development.**

`imgopt` is a high-performance, accessibility-first CLI tool designed to batch convert and optimize images (PNG, JPG, TIFF) into efficient **WebP** format. It utilizes concurrency to process thousands of images in seconds and features a smart resizing engine that preserves aspect ratio.

## Features ✨

* **⚡ Fast:** Uses multi-core processing (`ProcessPoolExecutor`) to utilize 100% of your CPU power.
* **🧠 Smart:** Auto-resizes images to a standard web width (default 1920px) without distortion. You can also skip resizing completely.
* **🔍 Recursive:** Automatically scans all subfolders and replicates the structure in the output.
* **🛡️ Safe:** Never overwrites your original files. Creates a new folder for optimized images.
* **♿ Accessible:** Optimized for screen readers (NVDA/JAWS) with clean logging and optional audio cues upon completion.
* **🧙‍♂️ Wizard Mode:** Don't like memorizing commands? Just run `imgopt` to enter an interactive step-by-step wizard.

## Installation 📦

You can install `imgopt` easily using `pip` or `uv`:

### Option 1: Using pip (Standard)
```bash
pip install imgopt-cli

### Option 2: Using uv (Recommended for speed)
```bash
uv tool install imgopt-cli
```
Note: The package name is imgopt-cli, but the command you run is simply imgopt.

## Usage 🛠️
1. Interactive Wizard (Recommended for beginners)
Just run the command without arguments. The tool will guide you step-by-step:
```bash
imgopt
```
2. Quick CLI Mode (For Pros)
Optimize a folder immediately with default settings (Quality: 80, Width: 1920px):
```bash
imgopt ./photos
```
3. Advanced Examples
Keep original size (No resizing):
```bash
imgopt ./photos -w 0
```
Custom quality and output folder:
```bash
imgopt ./raw_images --output ./web_ready --quality 90
```
Silent mode (Good for scripts):
```bash
imgopt ./assets --quiet --no-sound
```
## Options ⚙️

| Flag            | Description                                                     |
| :-------------- | :-------------------------------------------------------------- |
| `-i, --interactive` | Force the interactive wizard mode.                              |
| `-q, --quality`   | Set WebP quality (0-100). Default is 80.                        |
| `-w, --width`     | Max width in pixels. Use 0 to keep original dimensions. Default is 1920. |
| `-o, --output`    | Custom name for the output folder. Default is optimized_webp.   |
| `--quiet`       | Suppress per-file logs (show only final summary).               |
| `--no-sound`    | Disable the "beep" notification sound at the end.               |
| `--version`     | Show the current version.                                       |

## Requirements
* Python 3.8+
* Pillow (Installed automatically)

## License
This project is licensed under the MIT License. See LICENSE for details.

## Support 💖
If you find this tool useful, please consider giving it a ⭐ on GitHub!