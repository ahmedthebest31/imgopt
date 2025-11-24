import argparse
import sys
import time
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from PIL import Image

# --- Configuration ---
EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}

def log(message, force=False, verbose=True):
    """
    Handles printing to the screen.
    - force: Always print this message (e.g., errors or final summary).
    - verbose: Only print if the user requested detailed logs.
    """
    if force or verbose:
        print(message)

def get_input(prompt, default_value=None):
    """Helper for interactive input with defaults."""
    if default_value:
        user_input = input(f"{prompt} (Default: {default_value}): ").strip()
        return user_input if user_input else default_value
    else:
        return input(f"{prompt}: ").strip()

def process_single_image(args_tuple):
    """
    Process a single image. Designed for parallel execution.
    Args: (file_path, output_root, input_root, quality, max_width)
    """
    file_path, output_root, input_root, quality, max_width = args_tuple
    
    try:
        # Determine relative path to maintain folder structure in output
        # e.g., input/2024/img.jpg -> output/2024/img.webp
        relative_path = file_path.relative_to(input_root)
        output_file_path = output_root / relative_path.with_suffix('.webp')
        
        # Ensure the sub-folder exists
        output_file_path.parent.mkdir(parents=True, exist_ok=True)

        original_size = file_path.stat().st_size
        
        with Image.open(file_path) as img:
            # Smart Resize Logic
            if max_width and img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # Save as WebP
            img.save(
                output_file_path, 
                'webp', 
                quality=quality, 
                method=6  # Max compression effort
            )
            
        new_size = output_file_path.stat().st_size
        saved = original_size - new_size
        
        return (True, file_path.name, original_size, new_size)

    except Exception as e:
        return (False, f"{file_path.name}: {str(e)}", 0, 0)

def main():
    parser = argparse.ArgumentParser(description="Image Optimizer (WebP Converter)")
    parser.add_argument("-i", "--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("path", nargs="?", help="Input folder path")
    parser.add_argument("--quiet", action="store_true", help="Suppress detailed per-file output")
    
    args = parser.parse_args()

    # --- Variables Init ---
    input_path_str = ""
    target_width = 1920
    output_folder_name = "optimized_webp"
    quality = 80
    verbose = not args.quiet # Default is verbose unless --quiet is used
    is_interactive = args.interactive

    # --- Auto-Interactive Trigger ---
    # If no path is provided and no flags are set, force interactive mode
    if len(sys.argv) == 1:
        is_interactive = True

    # --- Interactive Logic ---
    if is_interactive:
        print("\n--- Image Optimizer Tool ---")
        
        # 1. Get Path
        while not input_path_str:
            input_path_str = get_input("Enter input folder path")
            if not input_path_str:
                print("Error: Path is required.")

        # 2. Get Width
        width_input = get_input("Max image width", default_value="1920")
        try:
            target_width = int(width_input)
        except ValueError:
            print("Invalid number. Using 1920.")
            target_width = 1920

        # 3. Output Folder
        output_folder_name = get_input("Output folder name", default_value="optimized_webp")

        # 4. Verbose Choice (The feature you requested)
        show_details = get_input("Show detailed progress for every file? (y/n)", default_value="n").lower()
        verbose = show_details.startswith('y')
        
    else:
        # CLI Mode check
        if not args.path:
            # This part is technically unreachable due to Auto-Interactive logic, 
            # but kept for safety.
            print("Usage: imgopt <path> [options]")
            return
        input_path_str = args.path

    # --- Setup Paths ---
    input_dir = Path(input_path_str)
    if not input_dir.exists():
        print(f"Error: Directory '{input_dir}' not found.")
        return

    output_dir = input_dir / output_folder_name
    output_dir.mkdir(exist_ok=True)

    # --- Recursive Search (rglob) ---
    print("Scanning files...")
    # Exclude the output folder itself to avoid infinite loops if it's inside input
    files = [
        f for f in input_dir.rglob("*") 
        if f.suffix.lower() in EXTENSIONS 
        and f.is_file() 
        and output_folder_name not in f.parts
    ]

    if not files:
        print("No supported images found.")
        return

    # --- Pre-run Summary ---
    print("-" * 40)
    print(f"Source:      {input_dir}")
    print(f"Destination: {output_dir}")
    print(f"Image Count: {len(files)}")
    print(f"Max Width:   {target_width}px")
    print(f"Verbose:     {'Yes' if verbose else 'No'}")
    print("-" * 40)
    print("Processing started... Please wait.")

    start_time = time.time()
    
    # Prepare Tasks
    # passing input_dir as well to calculate relative paths
    tasks = [(f, output_dir, input_dir, quality, target_width) for f in files]

    success_count = 0
    fail_count = 0
    total_original_size = 0
    total_new_size = 0

    # --- Parallel Execution ---
    try:
        with ProcessPoolExecutor() as executor:
            results = executor.map(process_single_image, tasks)
            
            for result in results:
                is_success, msg, orig_size, new_size = result
                
                if is_success:
                    success_count += 1
                    total_original_size += orig_size
                    total_new_size += new_size
                    log(f"[OK] {msg}", verbose=verbose)
                else:
                    fail_count += 1
                    # Always print errors even in quiet mode
                    log(f"[FAILED] {msg}", force=True)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user!")
        sys.exit()

    end_time = time.time()
    duration = end_time - start_time
    
    # --- Final Stats Calculation ---
    total_saved = total_original_size - total_new_size
    saved_mb = total_saved / (1024 * 1024)
    original_mb = total_original_size / (1024 * 1024)
    new_mb = total_new_size / (1024 * 1024)
    
    if total_original_size > 0:
        saved_percent = (total_saved / total_original_size) * 100
    else:
        saved_percent = 0

    # --- Final Report ---
    print("\n" + "=" * 40)
    print("       OPTIMIZATION COMPLETE       ")
    print("=" * 40)
    print(f"Total Images:    {len(files)}")
    print(f"Successful:      {success_count}")
    print(f"Failed:          {fail_count}")
    print("-" * 40)
    print(f"Original Size:   {original_mb:.2f} MB")
    print(f"Optimized Size:  {new_mb:.2f} MB")
    print(f"Space Saved:     {saved_mb:.2f} MB ({saved_percent:.1f}%)")
    print("-" * 40)
    print(f"Time Taken:      {duration:.2f} seconds")
    print(f"Output Location: {output_dir}")
    print("=" * 40)

    # Audio Notification (Beep)
    print('\a') 

if __name__ == "__main__":
    main()