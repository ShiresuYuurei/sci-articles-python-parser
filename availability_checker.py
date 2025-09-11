import requests
from urllib.parse import quote_plus
from typing import Dict, Any, List, Optional, final
from decorators import retry_on_failure
from playwright_utils import BrowserSession
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
import time
import random

REQUEST_TIMEOUT = 3
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CyberParser/1.0)"}

@retry_on_failure()
def publisher_availability(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Проверяет доступность статьи на сайте издателя.
    Возвращает словарь с признаками:
      - publisher_pdf: есть ли PDF у издателя
      - open_access: опубликована ли статья в открытом доступе
      - publisher_links: список доступных ссылок от издателя
    """
    links = item.get("link", [])
    pdf_links = [
        l for l in links
        if l.get("URL", "").lower().endswith(".pdf")
        or "pdf" in l.get("content-type", "").lower()
    ]

    has_pdf = False

    if pdf_links:
        with BrowserSession(headless=False) as session:
            page = session.context.new_page()

            for l in pdf_links:
                url = l.get("URL", "").strip()
                if not url:
                    continue
                try:
                    page.goto(url, timeout=20000, wait_until="domcontentloaded")

                    final_url = page.url.strip()

                    if final_url.lower() == url.lower():
                        has_pdf = True
                        break
                except Exception as e:
                    continue

    return {
        "publisher_pdf": has_pdf,
        "publisher_links": links
    }

@retry_on_failure()
def check_pirates(doi: str, pirate_bases: Optional[List[str]]) -> Dict[str, Any]:
    """
    Проверяет наличие статьи по DOI на пиратских ресурсах.
    Для каждого ресурса формируются возможные URL-запросы.
    Если ответ 200 и в HTML содержится DOI или PDF — статья считается найденной.
    Возвращает словарь:
      - pirates: словарь {ресурс: True/False}
      - pirates_any: общий флаг (нашлась ли где-либо)
    """
    if not pirate_bases:
        return {"pirates": {}, "pirates_any": False}

    doi_q: str = quote_plus(doi)
    found_any = False
    details = {}

    for base in pirate_bases:
        ok = False
        candidates = []

        if base.endswith("=") or base.endswith("/"):
            candidates.append(base + doi_q)
        else:
            candidates.append(base + "/" + doi_q)
            candidates.append(base + "?q=" + doi_q)

        for u in candidates:
            try:
                r: requests.Response = requests.get(u, headers=HEADERS, timeout=REQUEST_TIMEOUT)
                if r.status_code == 200 and doi.lower() in r.text.lower():
                    ok = True
                    break
                if r.status_code == 200 and ".pdf" in r.text.lower():
                    ok = True
                    break
            except (requests.RequestException, ConnectionError, TimeoutError):
                continue

        details[base] = ok
        if ok:
            found_any = True

    return {"pirates": details, "pirates_any": found_any}

@retry_on_failure()
def check_researchgate(title: str, doi: str) -> str:
    """
    Проверяет наличие статьи по DOI на ResearchGate.
    Возможные результаты:
      - "yes": статья точно найдена
      - "maybe": страница открылась, но DOI не найден в HTML
      - "unknown": ошибка или сайт недоступен
    """
    with BrowserSession(headless=False) as session:
        try:
            page = session.context.new_page()
            url = f"https://www.researchgate.net/search/publication?q={quote_plus(title)}"

            time.sleep(random.uniform(0.1, 0.3))

            page.goto(url, timeout=40000)
            page.wait_for_selector(".nova-legacy-v-publication-item__stack", timeout=20000)

            content = page.content().lower()

            if doi.lower() in content:
                return "yes"
            else:
                return "no"
        except PlaywrightTimeoutError:
            return "unknown"
        except Exception as e:
            print(f"Error checking ResearchGate for {doi}: {e}")
            return "unknown"
