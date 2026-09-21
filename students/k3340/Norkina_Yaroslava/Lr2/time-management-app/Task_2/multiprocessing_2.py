import time
import multiprocessing
import requests
from requests.exceptions import RequestException

from parsing import load_urls, divide_into_chunks, extract_page_info
from db import save_to_db_sync

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}

def parse_and_save(url: str):
    # Целевая функция загрузки и обработки веб-страницы
    for attempt in range(3):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            
            page_data = extract_page_info(response.text, url)
            if page_data["title"] == "Без названия":
                return
                
            save_to_db_sync(page_data)
            print(f"[Process-{multiprocessing.current_process().name}] Сохранено: '{page_data['title']}'")
            return 
        except RequestException:
            time.sleep(1)
        except Exception as e:
            print(f"[Process-{multiprocessing.current_process().name}] Ошибка: {e}")
            return

def process_worker(urls_chunk: list[str]):
    # Работа процесса
    for url in urls_chunk:
        parse_and_save(url)

def run_multiprocessing() -> float:
    # Многопроцессное выполнение
    print("Запуск процессов")
    start_time = time.time()
    
    urls = load_urls()
    num_processes = 8
    chunks = divide_into_chunks(urls, num_processes)
    processes = []
    
    # Создание изолированных процессов ОС. 
    # В отличие от потоков, процессы требуют больше ресурсов на инициализацию.
    for i, chunk in enumerate(chunks):
        p = multiprocessing.Process(target=process_worker, args=(chunk,), name=str(i+1))
        processes.append(p)
        p.start()
        
    for p in processes:
        p.join()
        
    elapsed = time.time() - start_time
    print(f"multiprocessing - завершено за {elapsed:.4f} сек\n")
    return elapsed