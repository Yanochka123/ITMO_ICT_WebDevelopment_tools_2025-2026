import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
import traceback

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from threading_2 import run_threading
from multiprocessing_2 import run_multiprocessing
from async_2 import run_asyncio
from db import clean_db_sync

from parsing import load_urls, divide_into_chunks, extract_page_info
from db import save_to_db_sync, save_to_db_async, clean_db_sync

import httpx

app = FastAPI(
    title="Parser Service",
    description="Сервис парсинга веб-страниц для тайм-менеджера",
    version="1.0.0",
)

# Схемы

class ParseRequest(BaseModel):
    url: str
    save_to_db: bool = True


class ParseResponse(BaseModel):
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    estimated_hours: Optional[float] = None
    category_hint: Optional[str] = None
    keywords: List[str] = []
    saved: bool = False
    status: str = "ok"
    error: Optional[str] = None


class BatchParseRequest(BaseModel):
    urls: List[str]
    save_to_db: bool = True


# Эндпоинты

@app.get("/health")
def health():
    return {"status": "ok", "service": "parser"}


@app.post("/parse", response_model=ParseResponse)
def parse_url(payload: ParseRequest):
    """Спарсить одну страницу и (опционально) сохранить в БД."""
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            response = client.get(payload.url)
            response.raise_for_status()
            html = response.text

        page_data = extract_page_info(html, payload.url)

        saved = False
        if payload.save_to_db:
            save_to_db_sync(page_data)
            saved = True

        return ParseResponse(
            url=payload.url,
            title=page_data["title"],
            description=page_data["description"],
            priority=page_data["priority"],
            estimated_hours=page_data["estimated_hours"],
            category_hint=page_data["category_hint"],
            keywords=page_data["keywords"],
            saved=saved,
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"HTTP error: {e}")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/parse/batch")
def parse_batch(payload: BatchParseRequest, background_tasks: BackgroundTasks):
    """Массовый парсинг в фоне."""
    background_tasks.add_task(_run_batch, payload.urls, payload.save_to_db)
    return {"status": "started", "count": len(payload.urls)}


def _run_batch(urls: List[str], save_to_db: bool):
    with httpx.Client(timeout=15, follow_redirects=True) as client:
        for url in urls:
            try:
                response = client.get(url)
                response.raise_for_status()
                page_data = extract_page_info(response.text, url)
                if save_to_db:
                    save_to_db_sync(page_data)
                print(f"[Batch] Сохранено: {page_data['title']}")
            except Exception as e:
                print(f"[Batch] Ошибка на {url}: {e}")


@app.post("/parse/file")
def parse_file(save_to_db: bool = True):
    """Спарсить все URL из urls.txt."""
    urls = load_urls()
    if not urls:
        raise HTTPException(status_code=404, detail="urls.txt пуст или не найден")
    chunks = divide_into_chunks(urls, 8)
    background_tasks = BackgroundTasks()
    for chunk in chunks:
        background_tasks.add_task(_run_batch, chunk, save_to_db)
    return {"status": "started", "total_urls": len(urls), "chunks": len(chunks)}


@app.post("/clean")
def clean():
    """Очистить данные парсера в БД."""
    clean_db_sync()
    return {"status": "cleaned"}




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
