import time
import argparse
import threading

def calculate_sum(start: int, end: int, results_list: list, index: int):
    # функция ничего не возвращает, так как имеет доступ к общим ресурсам процесса и может менять значение напрямую
    total = 0
    '''
    for i in range(start, end + 1):
        total += i
    '''
    # вычисление по формуле Гаусса позволяет получить результат за небольшое время
    total = (start + end)*(end - start + 1)//2
    results_list[index] = total

def run_threading(target_number: int, num_tasks: int):
    step = target_number // num_tasks
    threads = []
    results = [0] * num_tasks 

    print(f"Вычисление от 1 до {target_number} многопоточно, {num_tasks} потоков")
    start_time = time.time()
    
    for i in range(num_tasks):
        start = i * step + 1
        end = (i + 1) * step if i != num_tasks - 1 else target_number
        
        thread = threading.Thread(target=calculate_sum, args=(start, end, results, i))
        threads.append(thread)
        thread.start() # запуск каждого нового потока 
        
    for thread in threads:
        thread.join() # ожидание результата от всех потоков и завершение работы
            
    result = sum(results)
    timespent = time.time() - start_time
    
    print(f"Threading результат:  {result}, {timespent:.4f} сек")
    return result, timespent

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Многопоточное вычисление суммы")
    parser.add_argument("-n", type=int, default=10**6, help="Целевое число")
    parser.add_argument("-p", type=int, default=8, help="Количество потоков")
    args = parser.parse_args()
    
    run_threading(args.number, args.process)