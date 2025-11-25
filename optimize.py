import argparse
import sys
import time
import os
import signal
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from PIL import Image

# --- Version Info ---
__version__ = "1.0.0"

# --- Configuration ---
EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}

def signal_handler(sig, frame):
    """Handle termination signals gracefully."""
    print("\n[!] Process interrupted by system. Exiting...")
    sys.exit(1)

# Register system signals
signal.signal(signal.SIGINT, signal_handler)
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, signal_handler)

def log(message, force=False, verbose=True):
    if force or verbose:
        print(message)

def get_input(prompt, default_value=None):
    if default_value:
        user_input = input(f"{prompt} (Default: {default_value}): ").strip()
        return user_input if user_input else default_value
    else:
        return input(f"{prompt}: ").strip()

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
        return (False, f"{file_path.name}: {str(e)}", 0, 0)

def main():
    parser = argparse.ArgumentParser(description="Image Optimizer (WebP Converter)")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-i", "--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("path", nargs="?", help="Input folder path")
    parser.add_argument("--quiet", action="store_true", help="Suppress detailed per-file output")
    
    args = parser.parse_args()

    # Variables Init
    input_path_str = ""
    target_width = 1920
    output_folder_name = "optimized_webp"
    quality = 80
    verbose = not args.quiet
    is_interactive = args.interactive

    # Auto-Interactive Logic
    if len(sys.argv) == 1:
        is_interactive = True

    if is_interactive:
        print(f"\n--- Image Optimizer Tool v{__version__} ---")
        while not input_path_str:
            input_path_str = get_input("Enter input folder path")
            if not input_path_str:
                print("Error: Path is required.")
        
        try:
            target_width = int(get_input("Max image width", default_value="1920"))
        except ValueError:
            target_width = 1920
            
        output_folder_name = get_input("Output folder name", default_value="optimized_webp")
        show_details = get_input("Show detailed progress? (y/n)", default_value="n").lower()
        verbose = show_details.startswith('y')
    else:
        if not args.path:
            print("Usage: imgopt <path> [options]")
            sys.exit(1) # Exit with error code
        input_path_str = args.path

    input_dir = Path(input_path_str)
    if not input_dir.exists():
        print(f"Error: Directory '{input_dir}' not found.")
        sys.exit(1) # Exit with error code

    output_dir = input_dir / output_folder_name
    output_dir.mkdir(exist_ok=True)

    print("Scanning files...")
    files = [
        f for f in input_dir.rglob("*") 
        if f.suffix.lower() in EXTENSIONS 
        and f.is_file() 
        and output_folder_name not in f.parts
    ]

    if not files:
        print("No supported images found.")
        sys.exit(0) # Exit success (nothing to do is not an error)

    print("-" * 40)
    print(f"Processing {len(files)} images...")
    
    start_time = time.time()
    tasks = [(f, output_dir, input_dir, quality, target_width) for f in files]
    success_count = 0
    fail_count = 0
    total_original = 0
    total_new = 0

    with ProcessPoolExecutor() as executor:
        results = executor.map(process_single_image, tasks)
        for is_success, msg, orig, new_s in results:
            if is_success:
                success_count += 1
                total_original += orig
                total_new += new_s
                log(f"[OK] {msg}", verbose=verbose)
            else:
                fail_count += 1
                log(f"[FAILED] {msg}", force=True)

    end_time = time.time()
    
    # Final Stats
    saved_mb = (total_original - total_new) / (1024 * 1024)
    percent = (total_original - total_new) / total_original * 100 if total_original > 0 else 0
    
    print("\n" + "=" * 40)
    print(f"DONE. Success: {success_count} | Failed: {fail_count}")
    print(f"Saved: {saved_mb:.2f} MB ({percent:.1f}%)")
    print("=" * 40)
    print('\a') 
    
    # Exit code logic: If everything failed, return error code
    if success_count == 0 and len(files) > 0:
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()