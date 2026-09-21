import argparse

from task_1_threading import run_threading
from task_1_multiprocessing import run_multiprocessing
from task_1_async import run_asyncio

def main():
    parser = argparse.ArgumentParser(description="Задача 1")
    parser.add_argument("-n", "--number", type=int, default=10**6, help="Число для вычисления")
    parser.add_argument("-p", "--process", type=int, default=8, help="Количество процессов")
    args = parser.parse_args()

    print(f"Запуск с числом {args.number}, количество подходов - {args.process}")

    results_time = {}
    results_math = {}
    
    results_math["Threading"], results_time["Threading"] = run_threading(args.number, args.process)
    results_math["Multiprocessing"], results_time["Multiprocessing"] = run_multiprocessing(args.number, args.process)
    results_math["Async"], results_time["Async"] = run_asyncio(args.number, args.process)

    print(f"{'Подход':<20} | {'Время':<15}")
    for approach, time_taken in sorted(results_time.items(), key=lambda item: item[1]):
        print(f"{approach:<20} | {time_taken:.4f} сек")

if __name__ == "__main__":
    main()