# imgopt 🚀

**The Intelligent WebP Converter for Modern Web Development.**

`imgopt` is a high-performance, accessibility-first CLI tool designed to batch convert and optimize images (PNG, JPG, TIFF) into efficient WebP format. It features smart resizing, concurrency for speed, and an interactive wizard mode.

## Features ✨

-   **Batch Processing:** Convert hundreds of images in seconds using multi-core processing.
-   **Smart Resizing:** Automatically downscale images to a target width (e.g., 1920px) while maintaining aspect ratio.
-   **Interactive Wizard:** No need to memorize flags; just run `imgopt` and follow the prompts.
-   **Accessibility Friendly:** Screen-reader friendly outputs and audio cues upon completion.
-   **Safe:** Never overwrites your original files.

## Installation 📦

You can install `imgopt` directly from PyPI (coming soon) or from source:

```bash
pip install .
```

## Usage 🛠️

### Interactive Mode (Wizard)
Just run the command without arguments:
```bash
imgopt
```

### Quick CLI Mode
Optimize all images in a folder to 80% quality WebP, max width 1920px:
```bash
imgopt ./photos
```

### Advanced Usage
```bash
# Custom output folder, no resizing, 90% quality
imgopt ./raw_images --output ./web_ready --width 0 --quality 90

# Quiet mode (no per-file logs)
imgopt ./assets --quiet
```

## Requirements
-   Python 3.8+
-   Pillow

## License
MIT License. See [LICENSE](LICENSE) for details.
