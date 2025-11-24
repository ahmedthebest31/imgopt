import os
import sys
import time
from pathlib import Path
from PIL import Image

# دالة لطباعة النصوص بطريقة متوافقة مع قارئ الشاشة (سطر بسطر)
def log(message):
    print(message)

def optimize_images_for_web(input_path, quality=80):
    # تحويل المدخل إلى كائن مسار للتعامل الذكي مع النصوص
    input_dir = Path(input_path)
    
    if not input_dir.exists():
        log(f"خطأ: المجلد '{input_path}' غير موجود.")
        return

    # إنشاء مجلد للمخرجات داخل المجلد الأصلي باسم 'optimized_webp'
    output_dir = input_dir / "optimized_webp"
    output_dir.mkdir(exist_ok=True)

    # قائمة الامتدادات المدعومة
    extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    
    # جلب جميع الملفات
    files = [f for f in input_dir.iterdir() if f.suffix.lower() in extensions and f.is_file()]

    if not files:
        log("لم يتم العثور على صور في هذا المجلد.")
        return

    log(f"تم العثور على {len(files)} صورة. جاري البدء بأقصى إعدادات ضغط...")
    log("-" * 30)

    success_count = 0
    total_saved_space = 0

    for file_path in files:
        try:
            # فتح الصورة
            with Image.open(file_path) as img:
                # تحديد اسم الملف الجديد (بدون الامتداد القديم)
                # file.stem تأتي بالاسم فقط (مثلا image من image.png)
                new_filename = f"{file_path.stem}.webp"
                output_file_path = output_dir / new_filename

                # حساب الحجم الأصلي
                original_size = file_path.stat().st_size

                # --- قلب السحر هنا ---
                # method=6: أقصى جهد للضغط (أفضل نتيجة ممكنة)
                # quality=quality: الجودة المطلوبة (80 هو المعيار الذهبي للويب)
                img.save(
                    output_file_path, 
                    'webp', 
                    quality=quality, 
                    method=6
                )
                
                # حساب الحجم الجديد
                new_size = output_file_path.stat().st_size
                saved = original_size - new_size
                total_saved_space += saved
                
                # طباعة تقرير مختصر لكل ملف
                log(f"تم: {file_path.name} -> {new_filename}")
                # log(f"   وفرت: {saved / 1024:.1f} KB") 

                success_count += 1

        except Exception as e:
            log(f"فشل في معالجة {file_path.name}: {str(e)}")

    log("-" * 30)
    log("اكتملت العملية.")
    log(f"تم تحويل {success_count} من أصل {len(files)} صورة.")
    log(f"إجمالي المساحة التي تم توفيرها: {total_saved_space / 1024 / 1024:.2f} ميجابايت")
    log(f"مسار الصور الجديدة: {output_dir}")

if __name__ == "__main__":
    # التعامل مع الـ Arguments ليكون CLI محترم
    if len(sys.argv) < 2:
        log("طريقة الاستخدام:")
        log("python optimize.py <path_to_images_folder>")
    else:
        folder_path = sys.argv[1]
        optimize_images_for_web(folder_path)