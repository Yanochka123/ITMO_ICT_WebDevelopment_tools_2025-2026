import time
import argparse
import multiprocessing

def calculate_sum(args: tuple) -> int:
    # tuple на вход так как pool.map передает единственный аргумент
    start, end = args
    total = 0
    '''
    for i in range(start, end + 1):
        total += i
    '''
    # вычисление по формуле Гаусса позволяет получить результат за небольшое время
    total = (start + end)*(end - start + 1)//2
    
    return total

def run_multiprocessing(target_number: int, num_tasks: int):
    step = target_number // num_tasks
    tasks_args = []
    print(f"Вычисление от 1 до {target_number} multiprocessing, {num_tasks} процессов")

    start_time = time.time()

    for i in range(num_tasks):
        start = i * step + 1
        end = (i + 1) * step if i != num_tasks - 1 else target_number
        tasks_args.append((start, end))

    # использование библиотеки multiprocesing
    with multiprocessing.Pool(processes=num_tasks) as pool:
        results = pool.map(calculate_sum, tasks_args) # принимает в качестве аргументов целевую 
        # функцию и ее аргументы на вход единственной переменной
            
    result = sum(results)
    timespent = time.time() - start_time
    
    print(f"Multiprocessing результат:  {result}, {timespent:.4f} сек")
    return result, timespent

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multiprocessing вычисление суммы")
    parser.add_argument("-n", type=int, default=10**6, help="Целевое число")
    parser.add_argument("-p", type=int, default=8, help="Количество потоков")
    args = parser.parse_args()
    
    run_multiprocessing(args.number, args.process)