import requests
import time
from typing import Dict, Any, List, Optional

CROSSREF_BASE = "https://api.crossref.org/works"
REQUEST_TIMEOUT = 3
MAX_RETRIES = 3
RETRY_DELAY = 1.0
USER_AGENT = "CyberParser/1.0 (mailto:your_email@example.com)"

def safe_get(url: str, params: Optional[Dict[str,Any]] = None,
             headers: Optional[Dict[str, str]] = None) -> Optional[requests.Response]:
    """
    Безопасный GET-запрос с повторными попытками.
    Используется для защиты от временных сбоев сети или API.
    """
    for attempt in range(MAX_RETRIES):
        try:
            r: requests.Response = requests.get(url, params=params, headers=headers or {}, timeout=REQUEST_TIMEOUT)
            return r
        except (requests.RequestException, ConnectionError, TimeoutError):
            time.sleep(RETRY_DELAY)
    return None

def build_params(issn: Optional[str], query: str,
                 date_from: Optional[str], date_to: Optional[str],
                 rows: int = 100, offset: int = 0) -> Dict[str, Any]:
    """
    Формирует словарь параметров для запроса в CrossRef API.
    Поддерживает:
      - фильтрацию по ISSN
      - ограничение по датам публикации
      - пагинацию (rows, offset)
    """
    filters = []
    if issn:
        filters.append("issn:" + issn)
    if date_from:
        filters.append("from-pub-date:" + date_from.split("T")[0])
    if date_to:
        filters.append("until-pub-date:" + date_to.split("T")[0])
    params = {
        "filter": ",".join(filters) if filters else None,
        "query": query,
        "rows": rows,
        "offset": offset
    }
    # убираем None, чтобы не отправлять пустые параметры
    return {k:v for k,v in params.items() if v is not None}

def fetch_for_keyword(issn: str, keyword: str,
                      date_from: str, date_to: str,
                      rows: int = 100) -> List[Dict[str, Any]]:
    """
    Выполняет поиск статей в CrossRef API по одному ключевому слову.
    Возвращает список публикаций (items).
    """
    offset = 0
    results = []
    headers = {"User-Agent": USER_AGENT}

    while True:
        params: Dict[str, Any] = build_params(issn, keyword, date_from, date_to, rows=rows, offset=offset)
        r: Optional[requests.Response] = safe_get(CROSSREF_BASE, params=params, headers=headers)
        if r is None or r.status_code != 200:
            break

        j: Dict[str, Any] = r.json()
        items: List[Dict[str, Any]] = j.get("message", {}).get("items", [])
        if not items:
            break

        results.extend(items)

        # Поддержка пагинации: увеличиваем offset
        fetched = len(items)
        offset += fetched

        total: Optional[int] = j.get("message", {}).get("total-results")

        # Если данных больше нет — выходим
        if fetched < rows or (total is not None and offset >= total):
            break

        # небольшая задержка, чтобы не перегружать API
        time.sleep(0.1)

    return results

def collect_unique_by_doi(issn: str, keywords: List[str],
                          date_from: str, date_to: str,
                          rows: int = 100) -> Dict[str, Any]:
    """
    Главная функция модуля. Выполняет поиск по ISSN и ключевым словам.
    Результаты собираются в словарь по уникальным DOI.
    Если один и тот же DOI найден несколько раз, сохраняется запись с наибольшим количеством цитирований.
    """
    doi_data = {}
    for kw in keywords:
        items: List[Dict[str, Any]] = fetch_for_keyword(issn, kw, date_from, date_to, rows=rows)
        for it in items:
            doi: str = it.get("DOI", "")
            if not doi:
                continue

            doi_norm = doi.strip().lower()
            if doi_norm not in doi_data:
                doi_data[doi_norm] = it
            else:
                # если встретился тот же DOI, обновляем запись,
                # если у новой версии больше цитирований
                if it.get("is-referenced-by-count", 0) > doi_data[doi_norm].get("is-referenced-by-count", 0):
                    doi_data[doi_norm] = it
    return doi_data