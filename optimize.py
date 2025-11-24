import argparse
import sys
import time
from pathlib import Path
from PIL import Image
from concurrent.futures import ProcessPoolExecutor

# --- إعدادات ثابتة ---
EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}

def log(message):
    """طباعة متوافقة مع قارئ الشاشة"""
    print(message)

def get_input(prompt, default_value=None):
    """دالة مساعدة لأخذ المدخلات من المستخدم مع قيمة افتراضية"""
    if default_value:
        user_input = input(f"{prompt} (الافتراضي: {default_value}): ").strip()
        return user_input if user_input else default_value
    else:
        return input(f"{prompt}: ").strip()

def process_single_image(args_tuple):
    """معالجة صورة واحدة (مصممة لتعمل بشكل متوازي)"""
    file_path, output_dir, quality, max_width = args_tuple
    
    try:
        with Image.open(file_path) as img:
            # منطق تغيير الحجم الذكي (يحافظ على النسبة والتناسب)
            # نقوم بالتصغير فقط إذا كان العرض الأصلي أكبر من العرض المطلوب
            if max_width and img.width > max_width:
                # حساب نسبة التصغير (العرض المطلوب / العرض الأصلي)
                ratio = max_width / img.width
                # حساب الطول الجديد بناءً على النسبة للحفاظ على الشكل
                new_height = int(img.height * ratio)
                # تنفيذ تغيير الحجم باستخدام فلتر عالي الجودة
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # تجهيز المسار الجديد
            new_filename = f"{file_path.stem}.webp"
            output_file_path = output_dir / new_filename
            
            # الحفظ
            img.save(
                output_file_path, 
                'webp', 
                quality=quality, 
                method=6
            )
            
        return (True, file_path.name)

    except Exception as e:
        return (False, f"{file_path.name}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="أداة ضغط الصور للويب")
    parser.add_argument("-i", "--interactive", action="store_true", help="تشغيل الوضع التفاعلي (سؤال وجواب)")
    parser.add_argument("path", nargs="?", help="مسار المجلد (في حالة عدم استخدام الوضع التفاعلي)")
    
    args = parser.parse_args()

    # متغيرات سنملؤها سواء من التيرمينال مباشرة أو من الوضع التفاعلي
    input_path_str = ""
    target_width = 1920 # القيمة القياسية المفضلة
    output_folder_name = "optimized_webp"
    quality = 80

    # --- المنطق التفاعلي ---
    if args.interactive:
        log("--- الوضع التفاعلي ---")
        
        # 1. طلب المسار
        while not input_path_str:
            input_path_str = get_input("أدخل مسار مجلد الصور")
            if not input_path_str:
                log("يجب إدخال مسار.")

        # 2. طلب العرض (مع افتراضي 1920)
        width_input = get_input("أدخل أقصى عرض للصورة", default_value="1920")
        try:
            target_width = int(width_input)
        except ValueError:
            log("قيمة غير صحيحة للعرض، سيتم استخدام 1920 تلقائياً.")
            target_width = 1920

        # 3. طلب اسم مجلد الإخراج
        output_folder_name = get_input("اسم مجلد الحفظ الجديد", default_value="optimized_webp")

    else:
        # وضع سطر الأوامر العادي السريع
        if not args.path:
            log("خطأ: يجب تحديد مسار المجلد أو استخدام الخيار -i للوضع التفاعلي.")
            log("مثال: python tool.py -i")
            return
        input_path_str = args.path

    # --- بدء المعالجة ---
    input_dir = Path(input_path_str)
    
    if not input_dir.exists():
        log(f"خطأ: المجلد '{input_dir}' غير موجود.")
        return

    output_dir = input_dir / output_folder_name
    output_dir.mkdir(exist_ok=True)

    # جلب الصور
    files = [f for f in input_dir.iterdir() if f.suffix.lower() in EXTENSIONS and f.is_file()]
    
    if not files:
        log("لم يتم العثور على صور مدعومة في المجلد.")
        return

    log("-" * 30)
    log(f"المجلد المختار: {input_dir}")
    log(f"عدد الصور: {len(files)}")
    log(f"أقصى عرض سيتم تطبيقه: {target_width} بكسل (مع الحفاظ على التناسب)")
    log(f"سيتم الحفظ في: {output_folder_name}")
    log("-" * 30)
    log("جاري المعالجة... يرجى الانتظار...")

    start_time = time.time()
    success_count = 0

    # تجهيز المهام للمعالجة المتوازية
    tasks = [(f, output_dir, quality, target_width) for f in files]

    # التنفيذ
    with ProcessPoolExecutor() as executor:
        results = executor.map(process_single_image, tasks)
        
        for result in results:
            status, msg = result
            if status:
                success_count += 1
                log(f"تم: {msg}")
            else:
                log(f"فشل: {msg}")

    end_time = time.time()
    duration = end_time - start_time

    log("-" * 30)
    log(f"اكتملت العملية.")
    log(f"تم تحويل {success_count} من أصل {len(files)} صورة.")
    log(f"الزمن المستغرق: {duration:.2f} ثانية.")
    log(f"مسار الصور الجديدة: {output_dir}")

if __name__ == "__main__":
    main()