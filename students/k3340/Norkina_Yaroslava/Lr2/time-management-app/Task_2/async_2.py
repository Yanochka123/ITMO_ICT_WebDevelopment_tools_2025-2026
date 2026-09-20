import time
import asyncio
import aiohttp

from parsing import load_urls, divide_into_chunks, extract_page_info
from db import save_to_db_async

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}

async def parse_and_save(url: str, session: aiohttp.ClientSession):
    # асинхронная функция использует неблокирующиеся GIL операции ввода-вывода

    for _ in range(3):
        try:
            # Асинхронный HTTP-запрос
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                html = await response.text()
                
                # Извлечение данных
                page_data = extract_page_info(html, url)
                if page_data["title"] == "Без названия":
                    return
                    
                # Асинхронное сохранение в БД
                await save_to_db_async(page_data)
                print(f"[Async] Сохранено: '{page_data['title']}'")
                return
        except (aiohttp.ClientError, asyncio.TimeoutError):
            await asyncio.sleep(1)
        except Exception as e:
            print(f"[Async] Ошибка: {e}")
            return

async def async_worker(urls_chunk: list[str], session: aiohttp.ClientSession):
    tasks = [asyncio.create_task(parse_and_save(url, session)) for url in urls_chunk]
    await asyncio.gather(*tasks)

async def run_async_logic() -> float:
    print("Запуск асинхронности")
    start_time = time.time()
    
    urls = load_urls()
    num_tasks = 8
    chunks = divide_into_chunks(urls, num_tasks)
    
    # Ограничиваем пул одновременных TCP-соединений на уровне коннектора,
    # чтобы избежать отказа в обслуживании (DDoS-эффект) со стороны целевых серверов.
    connector = aiohttp.TCPConnector(limit=30)
    
    # Единая сессия переиспользует базовое TCP-соединение для всех запросов
    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
        workers = [asyncio.create_task(async_worker(chunk, session)) for chunk in chunks]
        await asyncio.gather(*workers)
        
    elapsed = time.time() - start_time
    print(f"asyncio завершено за {elapsed:.4f} сек\n")
    return elapsed

def run_asyncio() -> float:
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return asyncio.run(run_async_logic())