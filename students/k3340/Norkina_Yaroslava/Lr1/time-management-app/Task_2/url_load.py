import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def normalize_title(title: str) -> str:
    t = title.lower()
    t = re.sub(r'\(.*?\)', '', t)
    t = re.sub(r'\[.*?\]', '', t)
    t = re.sub(r'[^a-zа-я0-9\s]', '', t)
    return t.strip()


def fetch_real_urls():
    print("Сбор 100 уникальных ссылок (50 Wikipedia + 50 GitHub Awesome)...")
    urls_file = Path(__file__).parent / "urls.txt"
    all_urls = []
    seen_titles = set()
    seen_urls = set()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # 1. Wikipedia — списки дел, привычек, техник продуктивности (50)
    try:
        print("[1/2] Парсинг Wikipedia (productivity-related lists)...")
        wiki_categories = [
            "https://en.wikipedia.org/wiki/List_of_productivity_software",
            "https://en.wikipedia.org/wiki/Getting_Things_Done",
            "https://en.wikipedia.org/wiki/Pomodoro_Technique",
            "https://en.wikipedia.org/wiki/Time_management",
            "https://en.wikipedia.org/wiki/GTD",
        ]
        for url in wiki_categories:
            if len(all_urls) >= 50:
                break
            try:
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, "html.parser")

                # Ищем ссылки на другие статьи Wikipedia
                for a_tag in soup.find_all("a", href=True):
                    if len(all_urls) >= 50:
                        break
                    href = a_tag["href"]
                    if not href.startswith("/wiki/"):
                        continue
                    if ":" in href:  # служебные страницы
                        continue
                    raw_title = a_tag.get_text(strip=True)
                    if not raw_title or len(raw_title) < 3:
                        continue

                    norm_title = normalize_title(raw_title)
                    full_url = f"https://en.wikipedia.org{href}"

                    if (
                        norm_title not in seen_titles
                        and full_url not in seen_urls
                        and len(norm_title) > 2
                    ):
                        seen_titles.add(norm_title)
                        seen_urls.add(full_url)
                        all_urls.append(
                            (f"[Wikipedia] {raw_title}", full_url)
                        )
            except Exception as e:
                print(f"  Ошибка на {url}: {e}")
    except Exception as e:
        print(f"Ошибка Wikipedia: {e}")

    # 2. GitHub Awesome Lists — списки задач и инструментов (50)
    try:
        print("[2/2] Парсинг GitHub Awesome Lists...")
        github_pages = [
            "https://github.com/awesome-selfhosted/awesome-selfhosted",
            "https://github.com/sindresorhus/awesome",
            "https://github.com/awesome-foss/awesome-sysadmin",
            "https://github.com/kamranahmedse/developer-roadmap",
        ]
        for page_url in github_pages:
            if len(all_urls) >= 100:
                break
            try:
                response = requests.get(page_url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, "html.parser")

                # Ищем ссылки на другие GitHub-репозитории
                for a_tag in soup.find_all("a", href=True):
                    if len(all_urls) >= 100:
                        break
                    href = a_tag["href"]
                    if not href.startswith("https://github.com/"):
                        continue
                    if href.count("/") != 4:  # только ссылки на репозитории
                        continue
                    raw_title = a_tag.get_text(strip=True)
                    if not raw_title or len(raw_title) < 3:
                        continue

                    norm_title = normalize_title(raw_title)
                    if (
                        norm_title not in seen_titles
                        and href not in seen_urls
                        and len(norm_title) > 2
                    ):
                        seen_titles.add(norm_title)
                        seen_urls.add(href)
                        all_urls.append(
                            (f"[GitHub] {raw_title}", href)
                        )
            except Exception as e:
                print(f"  Ошибка на {page_url}: {e}")
    except Exception as e:
        print(f"Ошибка GitHub: {e}")

    # Сохраняем результат
    with open(urls_file, "w", encoding="utf-8") as f:
        for title, link in all_urls:
            f.write(f"# Страница: {title}\n")
            f.write(f"{link}\n\n")

    print(f"Успешно собрано {len(all_urls)} строго уникальных ссылок!")
    print(f"Файл сохранён: {urls_file}")


if __name__ == "__main__":
    fetch_real_urls()