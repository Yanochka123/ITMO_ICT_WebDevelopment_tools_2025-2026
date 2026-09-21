import time
import argparse
import asyncio

async def calculate_sum_async(start: int, end: int) -> int:
    # вычисление сложением - большая нагрузка
    total = 0

    for i in range(start, end + 1):
        total += i
    '''
    # вычисление по формуле Гаусса позволяет получить результат за небольшое время
    total = (start + end)*(end - start + 1)//2
    '''
    return total

async def run_asyncio_logic(target_number: int, num_tasks: int):
    step = target_number // num_tasks
    tasks = []


    print(f"Вычисление от 1 до {target_number} асинхронно, {num_tasks} функций")
    start_time = time.time()
    for i in range(num_tasks):
        start = i * step + 1
        end = (i + 1) * step if i != num_tasks - 1 else target_number
        tasks.append(calculate_sum_async(start, end))
        
    results = await asyncio.gather(*tasks)
    total_result = sum(results)

    timespent = time.time() - start_time
    print(f"Async результат: {total_result}, {timespent:.4f} сек")
    return total_result, timespent

def run_asyncio(target_number: int, num_tasks: int):
    # запуск синхронной функции
    return asyncio.run(run_asyncio_logic(target_number, num_tasks))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Асинхронное вычисление суммы")
    parser.add_argument("-n", type=int, default=10**6, help="Целевое число")
    parser.add_argument("-p", type=int, default=8, help="Количество функций")
    args = parser.parse_args()
    
    run_asyncio(args.number, args.process)