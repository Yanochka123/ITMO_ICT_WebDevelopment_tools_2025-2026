from task2_threading import run_threading
from task2_multiprocessing import run_multiprocessing
from task2_async import run_asyncio
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
