#!/usr/bin/env python3
import argparse
import sys
import time
import os
import signal
import logging
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from PIL import Image

__version__ = "1.5.0"
EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}

# Simple logging setup
logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)
logger = logging.getLogger()

def signal_handler(sig, frame):
    logger.error("\nProcess interrupted. Exiting...")
    sys.exit(1)

signal.signal(signal.SIGINT, signal_handler)
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, signal_handler)

def get_input_with_validation(prompt, validation_func, default_value=None):
    while True:
        display_prompt = f"{prompt}"
        if default_value:
            display_prompt += f" (Default: {default_value})"
        
        user_input = input(f"{display_prompt}: ").strip()

        if user_input.lower() in ['q', 'quit', 'exit']:
            sys.exit(0)

        if not user_input and default_value:
            return default_value
        
        result = validation_func(user_input)
        if result is not None:
            return result
        
        logger.warning("Invalid input. Try again.")

def validate_path(path_str):
    if not path_str: return None
    path = Path(path_str).resolve()
    if path.exists():
        return path
    logger.warning(f"Path not found: {path_str}")
    return None

def validate_width(width_str):
    if not width_str: return None
    if width_str.lower() in ['0', 'n', 'no', 'skip']:
        return 'SKIP' 
    try:
        val = int(width_str)
        if val >= 0: return val if val > 0 else 'SKIP'
        return None
    except ValueError:
        return None

def validate_yes_no(val_str):
    if not val_str: return None
    if val_str.lower().startswith('y'): return True
    if val_str.lower().startswith('n'): return False
    return None

def get_unique_output_folder(base_folder, name):
    # Prevents file/folder name collision
    output_path = base_folder / name
    if output_path.exists() and output_path.is_file():
        counter = 1
        while True:
            new_name = f"{name}_{counter}"
            new_path = base_folder / new_name
            if not new_path.is_file():
                return new_path
            counter += 1
    return output_path

def process_single_image(args_tuple):
    file_path, output_root, input_root, quality, max_width = args_tuple
    
    try:
        relative_path = file_path.relative_to(input_root)
        output_file_path = output_root / relative_path.with_suffix('.webp')
        output_file_path.parent.mkdir(parents=True, exist_ok=True)

        original_size = file_path.stat().st_size
        
        with Image.open(file_path) as img:
            if max_width and img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            img.save(output_file_path, 'webp', quality=quality, method=6)
            
        new_size = output_file_path.stat().st_size
        return (True, file_path.name, original_size, new_size)

    except Exception as e:
        return (False, f"{file_path.name}: {e}", 0, 0)

def main():
    parser = argparse.ArgumentParser(description="Image Optimizer")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive Mode")
    parser.add_argument("path", nargs="?", help="Input folder")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode")
    
    args = parser.parse_args()

    # Defaults
    input_dir = None
    target_width = 1920
    output_folder_name = "optimized_webp"
    quality = 80
    verbose = not args.quiet
    is_interactive = args.interactive
    play_sound = True

    if len(sys.argv) == 1:
        is_interactive = True

    if is_interactive:
        logger.info(f"Image Optimizer v{__version__}")
        logger.info("Press 'q' to exit at any time.\n")
        
        input_dir = get_input_with_validation("Input folder path", validate_path)
        
        width_result = get_input_with_validation(
            "Max width (0 for original)",
            validate_width, 
            default_value="1920"
        )
        target_width = None if width_result == 'SKIP' else width_result

        output_folder_name = get_input_with_validation(
            "Output folder name", 
            lambda x: x if x else None, 
            default_value="optimized_webp"
        )

        verbose = get_input_with_validation(
            "Show details? (y/n)", 
            validate_yes_no, 
            default_value="n"
        )
        
        play_sound = get_input_with_validation(
            "Play sound when done? (y/n)", 
            validate_yes_no, 
            default_value="y"
        )
        
    else:
        if not args.path:
            parser.print_help()
            sys.exit(1)
        input_dir = validate_path(args.path)
        if not input_dir: sys.exit(1)

    output_dir = get_unique_output_folder(input_dir, output_folder_name)
    if input_dir == output_dir:
        logger.error("Error: Input and Output cannot be the same.")
        sys.exit(1)

    output_dir.mkdir(exist_ok=True)

    logger.info("Scanning...")
    files = [
        f for f in input_dir.rglob("*") 
        if f.suffix.lower() in EXTENSIONS 
        and f.is_file() 
        and output_dir not in f.parents
    ]

    if not files:
        logger.warning("No images found.")
        sys.exit(0)

    logger.info(f"Total Images: {len(files)}")
    logger.info(f"Resize: {target_width if target_width else 'Original'}")
    logger.info(f"Output: {output_dir.name}")
    
    start_time = time.time()
    tasks = [(f, output_dir, input_dir, quality, target_width) for f in files]
    
    success = 0
    failed = 0
    orig_total = 0
    new_total = 0

    try:
        with ProcessPoolExecutor() as executor:
            results = executor.map(process_single_image, tasks)
            for is_ok, msg, orig, new_s in results:
                if is_ok:
                    success += 1
                    orig_total += orig
                    new_total += new_s
                    if verbose: logger.info(f"Success: {msg}")
                else:
                    failed += 1
                    logger.error(f"Failed: {msg}")

    except KeyboardInterrupt:
        logger.error("\nCancelled.")
        sys.exit(1)

    saved = orig_total - new_total
    saved_mb = saved / (1024 * 1024)
    pct = (saved / orig_total * 100) if orig_total > 0 else 0
    
    logger.info("\nOptimization Complete")
    logger.info(f"Success: {success}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Saved: {saved_mb:.2f} MB ({pct:.1f}%)")
    logger.info(f"Path: {output_dir}")
    
    if play_sound: print('\a') 
    if success == 0 and len(files) > 0: sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()