import uuid
import math
import re
from pathlib import Path

from bs4 import BeautifulSoup


# Загружает URL-ы из текстового файла, игнорируя пустые строки и комментарии

def load_urls(filename: str = "urls.txt") -> list[str]:
    file_path = Path(__file__).parent / filename
    urls = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                url = line.strip()
                if url and not url.startswith("#"):
                    urls.append(url)
    except FileNotFoundError:
        print(f"[Ошибка] Файл {filename} не найден!")
    return urls

# Разделяет список на равные части

def divide_into_chunks(lst: list, num_chunks: int) -> list[list]:
    if not lst:
        return []
    chunk_size = math.ceil(len(lst) / num_chunks)
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


# Возвращает словарь, совместимый со схемой БД тайм-менеджера (tags, tasks, categories)

def extract_page_info(html: str, url: str) -> dict:
    """
    Получает на вход страницу с задачами
    
    Структура результата:
        {
            "external_id": str,       # уникальный ID импорта (uuid)
            "title": str,             # <title> страницы - tags.name
            "description": str,       # meta description - tasks.description
            "language": str,          # язык страницы
            "keywords": list[str],    # ключевые слова - tags
            "estimated_hours": float, # предполагаемая оценка времени
            "priority": str,          # low/medium/high/urgent/critical
            "category_hint": str,     # предполагаемая категория
            "url": str,               # исходный URL
        }
    """
    soup = BeautifulSoup(html, "html.parser")

    title = "Без названия"
    description = "Описание недоступно."
    language = "en"
    keywords: list[str] = []
    estimated_hours = 1.0
    priority = "medium"
    category_hint = "Прочее"

    if "wikipedia.org" in url:
        h1 = soup.find("h1", id="firstHeading")
        if h1:
            title = h1.get_text(strip=True)

        # Описание из первого параграфа
        content_div = soup.find("div", id="mw-content-text")
        if content_div:
            first_p = content_div.find("p")
            if first_p:
                description = first_p.get_text(separator=" ", strip=True)

        # Язык
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            language = html_tag["lang"]

        # Ключевые слова из категорий страницы
        cat_div = soup.find("div", id="catlinks")
        if cat_div:
            for a_tag in cat_div.find_all("a"):
                kw = a_tag.get_text(strip=True)
                if kw and kw.lower() not in {"categories", "hidden categories"}:
                    keywords.append(kw)

        # Предполагаемый приоритет по названию
        priority = _guess_priority(title)
        # Предполагаемая категория
        category_hint = _guess_category(title, keywords)


    elif "github.com" in url:
        # Название репозитория
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True).split(":")[0].strip()

        # Описание из meta
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"]

        # Topics (ключевые слова)
        for a_tag in soup.find_all("a", class_="topic-tag"):
            kw = a_tag.get_text(strip=True)
            if kw:
                keywords.append(kw)

        # Язык
        lang_meta = soup.find("meta", attrs={"http-equiv": "content-language"})
        if lang_meta and lang_meta.get("content"):
            language = lang_meta["content"]

        priority = _guess_priority(title)
        category_hint = _guess_category(title, keywords)


    # для остальных сайтов
    else:
        # 1. <title>
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # 2. meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if not meta_desc:
            meta_desc = soup.find("meta", attrs={"property": "og:description"})
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"]

        # 3. meta keywords
        meta_kw = soup.find("meta", attrs={"name": "keywords"})
        if meta_kw and meta_kw.get("content"):
            keywords = [k.strip() for k in meta_kw["content"].split(",") if k.strip()]

        # 4. Язык
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            language = html_tag["lang"]

        # 5. Приоритет и категория
        priority = _guess_priority(title + " " + description)
        category_hint = _guess_category(title, keywords)


    # Язык
    LANG_MAP = {
        "en": "English",
        "ru": "Russian",
        "fr": "French",
        "de": "German",
        "es": "Spanish",
        "it": "Italian",
        "nl": "Dutch",
        "pt": "Portuguese",
        "zh": "Chinese",
        "ja": "Japanese",
        "fi": "Finnish",
    }
    if language:
        raw_lang = language.lower().strip()
        base_lang = raw_lang.split("-")[0]
        language = LANG_MAP.get(base_lang, raw_lang.capitalize()[:10])
    else:
        language = "English"

    # Ключевые слова в tags.name
    if not keywords:
        keywords = ["imported", "web"]
    else:
        cleaned = []
        seen = set()
        for kw in keywords:
            clean_kw = re.sub(r"\s+", " ", kw).strip().title()
            if clean_kw and len(clean_kw) > 2 and clean_kw.lower() not in seen:
                seen.add(clean_kw.lower())
                cleaned.append(clean_kw[:100])
        keywords = cleaned[:5]
        if not keywords:
            keywords = ["imported", "web"]

    # Описание
    if description:
        description = re.sub(r"\s+", " ", description).strip()
        if len(description) > 1000:
            description = description[:997] + "..."

    # Оценка времени по длине описания
    # Чем длиннее описание — тем больше времени может потребоваться
    word_count = len(description.split())
    if word_count < 20:
        estimated_hours = 0.5
    elif word_count < 100:
        estimated_hours = 1.0
    elif word_count < 300:
        estimated_hours = 2.0
    else:
        estimated_hours = 4.0

    # Приоритет
    priority = _normalize_priority(priority)

    # Категория
    category_hint = category_hint[:50]

    return {
        "external_id": f"parsed-{uuid.uuid4().hex[:8]}",
        "title": title[:100],
        "description": description,
        "language": language[:10],
        "keywords": keywords,
        "estimated_hours": estimated_hours,
        "priority": priority,
        "category_hint": category_hint,
        "url": url,
    }

# Угадывает приоритет по ключевым словам в тексте

def _guess_priority(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["urgent", "critical", "asap", "срочно", "критично"]):
        return "urgent"
    if any(w in t for w in ["important", "high", "важно", "высокий"]):
        return "high"
    if any(w in t for w in ["low", "optional", "низкий", "опционально"]):
        return "low"
    return "medium"

# Приводит приоритет к значениям из PriorityLevel модели Task

def _normalize_priority(priority: str) -> str:
    allowed = {"low", "medium", "high", "urgent", "critical"}
    p = priority.lower().strip()
    return p if p in allowed else "medium"

# Угадывает категорию по названию и ключевым словам

def _guess_category(title: str, keywords: list[str]) -> str:
    text = (title + " " + " ".join(keywords)).lower()

    rules = [
        (["work", "project", "office", "работа", "проект"], "Работа"),
        (["study", "learn", "course", "учеб", "курс", "обуч"], "Обучение"),
        (["home", "house", "clean", "дом", "уборк"], "Дом"),
        (["health", "sport", "fitness", "здоров", "спорт"], "Здоровье"),
        (["finance", "money", "budget", "финанс", "бюджет"], "Финансы"),
        (["travel", "trip", "путешеств", "поездк"], "Путешествия"),
        (["shop", "buy", "покупк", "купить"], "Покупки"),
        (["productivity", "time", "plan", "продуктивность", "план"], "Продуктивность"),
    ]

    for words, category in rules:
        if any(w in text for w in words):
            return category

    return "Прочее"