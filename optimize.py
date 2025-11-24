import argparse
import time
from pathlib import Path
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
import os

# إعدادات افتراضية
DEFAULT_QUALITY = 80
EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}

def log(message):
    """طباعة رسائل متوافقة مع قارئ الشاشة"""
    print(message)

def process_single_image(file_info):
    """دالة تعالج صورة واحدة ليتم تشغيلها بشكل متوازي"""
    file_path, output_dir, quality, max_width = file_info
    
    try:
        img_name = file_path.stem
        new_filename = f"{img_name}.webp"
        output_file_path = output_dir / new_filename

        original_size = file_path.stat().st_size
        
        with Image.open(file_path) as img:
            # تغيير الحجم إذا تم طلب ذلك
            if max_width and img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # الحفظ بأقصى ضغط
            img.save(
                output_file_path, 
                'webp', 
                quality=quality, 
                method=6
            )
        
        new_size = output_file_path.stat().st_size
        saved = original_size - new_size
        return (True, file_path.name, saved)

    except Exception as e:
        return (False, file_path.name, str(e))

def main():
    parser = argparse.ArgumentParser(description="أداة ضغط الصور وتحويلها إلى WebP")
    
    # استقبال المدخلات عبر Flags
    parser.add_argument("input_path", help="مسار المجلد الذي يحتوي على الصور")
    parser.add_argument("-q", "--quality", type=int, default=80, help="جودة الصورة (من 1 إلى 100). الافتراضي 80")
    parser.add_argument("-w", "--width", type=int, help="أقصى عرض للصورة (اختياري)")
    parser.add_argument("-o", "--output", help="اسم مجلد المخرجات (اختياري)")
    
    args = parser.parse_args()

    input_dir = Path(args.input_path)

    if not input_dir.exists():
        log(f"خطأ: المسار '{input_dir}' غير موجود.")
        return

    # تحديد مجلد المخرجات
    output_folder_name = args.output if args.output else "optimized_webp"
    output_dir = input_dir / output_folder_name
    output_dir.mkdir(exist_ok=True)

    # جمع الملفات
    files = [f for f in input_dir.iterdir() if f.suffix.lower() in EXTENSIONS and f.is_file()]

    if not files:
        log("لم يتم العثور على صور.")
        return

    log(f"تم العثور على {len(files)} صورة.")
    log(f"الإعدادات: الجودة={args.quality}, أقصى عرض={args.width if args.width else 'أصلي'}")
    log("جاري المعالجة...")

    # تجهيز البيانات للمعالجة المتوازية
    # نمرر البيانات كـ Tuple لأن ProcessPoolExecutor يحتاج دالة بمدخل واحد غالباً للسهولة
    tasks = [(f, output_dir, args.quality, args.width) for f in files]

    success_count = 0
    total_saved = 0

    # استخدام المعالجة المتوازية لاستغلال كل أنوية المعالج لديك (Ryzen 6 Cores)
    with ProcessPoolExecutor() as executor:
        results = executor.map(process_single_image, tasks)
        
        for result in results:
            is_success, name, data = result
            if is_success:
                success_count += 1
                total_saved += data
                # طباعة بسيطة لكل ملف تنتهي معالجته
                log(f"تم: {name}") 
            else:
                log(f"فشل {name}: {data}")

    log("-" * 30)
    log(f"اكتملت العملية بنجاح لـ {success_count} صورة.")
    log(f"إجمالي المساحة الموفرة: {total_saved / 1024 / 1024:.2f} ميجابايت")
    log(f"المسار: {output_dir}")

if __name__ == "__main__":
    main()