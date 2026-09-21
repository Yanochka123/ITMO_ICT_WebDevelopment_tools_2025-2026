import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from threading_2 import run_threading
from multiprocessing_2 import run_multiprocessing
from async_2 import run_asyncio
from db import clean_db_sync


def main():
    print("Запуск парсинга\n")

    results = {}

    clean_db_sync()
    results["Threading"] = run_threading()

    clean_db_sync()
    results["Multiprocessing"] = run_multiprocessing()

    clean_db_sync()
    results["Asyncio"] = run_asyncio()

    print(f"{'Подход':<20} | {'Время (сек)':<15}")

    for approach, time_taken in sorted(results.items(), key=lambda item: item[1]):
        print(f"{approach:<20} | {time_taken:.4f} сек")


if __name__ == "__main__":
    main()
