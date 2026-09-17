# app/debug.py
import traceback
import sys
from datetime import datetime

def log_error(error_msg: str, exc_info=None):
    """Запись ошибки в файл и вывод в консоль"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Вывод в консоль
    print(f"\n{'='*60}")
    print(f"❌ ОШИБКА [{timestamp}]")
    print(error_msg)
    
    if exc_info:
        traceback.print_exc()
    
    print(f"{'='*60}\n")
    sys.stdout.flush()  # Принудительный сброс буфера
    
    # Запись в файл
    try:
        with open("debug.log", "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"❌ ОШИБКА [{timestamp}]\n")
            f.write(f"{error_msg}\n")
            if exc_info:
                f.write(traceback.format_exc())
            f.write(f"{'='*60}\n")
    except:
        pass