import time
import threading
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
            print(f"[Thread-{threading.current_thread().name}] Сохранено: '{page_data['title']}'")
            return 
        except RequestException:
            # При сетевом сбое (таймаут) поток засыпает перед повторной попыткой.
            # Благодаря GIL в этот момент управление передается другому потоку.
            time.sleep(1) 
        except Exception as e:
            print(f"[Thread-{threading.current_thread().name}] Ошибка: {e}")
            return

def thread_worker(urls_chunk: list[str]):
    # Работа потока
    for url in urls_chunk:
        parse_and_save(url)

def run_threading() -> float:
    # Начало многопоточного выполнения
    print("Запуск потоков")
    start_time = time.time()
    
    urls = load_urls()
    num_threads = 8
    chunks = divide_into_chunks(urls, num_threads)
    threads = []
    
    # Инициализация и запуск потоков в адресном пространстве одного процесса ОС
    for i, chunk in enumerate(chunks):
        t = threading.Thread(target=thread_worker, args=(chunk,), name=str(i+1))
        threads.append(t)
        t.start()
        
    # Блокировка основного потока исполнения до завершения работы всех дочерних
    for t in threads:
        t.join()
        
    timespent = time.time() - start_time
    print(f"Threading - завершено за {timespent:.4f} сек\n")
    return timespent