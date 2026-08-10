"""
Wildberries API Parser v2.0
Автор: IT Factory (Automation Division)
Назначение: Высокоскоростной сбор данных о товарах через скрытое API WB.
"""
import requests
import pandas as pd
import time
import logging
from fake_useragent import UserAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Конфигурация
SEARCH_API_URL = "https://search.wb.ru/exactmatch/ru/common/v9/search"
DEST = "-1257786"
CURRENCY = "rub"
LOCALE = "ru"
RATE_LIMIT_DELAY = 0.6

ua = UserAgent()

def get_headers():
    return {
        "User-Agent": ua.random,
        "Accept": "application/json",
        "Origin": "https://www.wildberries.ru",
        "Referer": "https://www.wildberries.ru/",
    }

def fetch_search(query: str, page: int = 1) -> dict:
    """Поиск товаров по ключевому запросу."""
    params = {
        "appType": 1,
        "curr": CURRENCY,
        "dest": DEST,
        "query": query,
        "page": page,
        "resultset": "catalog",
        "sort": "popular",
        "spp": 30,
        "locale": LOCALE,
    }
    resp = requests.get(SEARCH_API_URL, params=params, headers=get_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()

def parse_wildberries(query: str, max_pages: int = 1) -> list:
    """Сбор всех товаров по ключевому слову."""
    results = []
    logging.info(f"🚀 Старт парсинга по запросу: '{query}'")

    for page in range(1, max_pages + 1):
        try:
            data = fetch_search(query, page)
            products = data.get("data", {}).get("products", [])

            if not products:
                logging.info(f"⚠️ Страница {page} пуста. Завершаем сбор.")
                break

            for item in products:
                results.append({
                    "Артикул": item.get("id"),
                    "Бренд": item.get("brand"),
                    "Название": item.get("name"),
                    "Цена (руб)": item.get("salePriceU", 0) / 100,
                    "Рейтинг": item.get("rating"),
                    "Отзывы": item.get("feedbacks"),
                    "Остаток (шт)": item.get("volume", 0)
                })

            logging.info(f"✅ Страница {page} обработана. Собрано: {len(products)} товаров.")
            time.sleep(RATE_LIMIT_DELAY)

        except Exception as e:
            logging.error(f"❌ Ошибка на странице {page}: {e}")
            break

    return results

def save_to_excel(data: list, filename="wb_report.xlsx"):
    """Экспорт собранных данных в Excel-отчет."""
    if not data:
        logging.warning("📭 Нет данных для сохранения.")
        return

    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    logging.info(f"💾 Данные успешно сохранены в файл: {filename}")

if __name__ == "__main__":
    search_query = "мужские часы"
    parsed_data = parse_wildberries(search_query, max_pages=3)
    save_to_excel(parsed_data)
    print("🎉 Парсинг успешно завершен!")
