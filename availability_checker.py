import requests
from urllib.parse import quote_plus

REQUEST_TIMEOUT = 3
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CyberParser/1.0)"}

def publisher_availability(item):
    """
    Проверяет доступность статьи на сайте издателя.
    Возвращает словарь с признаками:
      - publisher_pdf: есть ли PDF у издателя
      - open_access: опубликована ли статья в открытом доступе
      - publisher_links: список доступных ссылок от издателя
    """
    links = item.get("link", [])
    has_pdf = False
    for l in links:
        url = l.get("URL","").lower()
        ctype = (l.get("content-type") or "").lower()
        if "pdf" in ctype or url.endswith(".pdf"):
            has_pdf = True
            break
    # Проверяем, есть ли у статьи лицензия (признак Открытого доступа)
    is_open = bool(item.get("license"))
    return {"publisher_pdf": has_pdf, "open_access": is_open, "publisher_links": links}

def check_pirates(doi, pirate_bases):
    """
    Проверяет наличие статьи по DOI на пиратских ресурсах.
    Для каждого ресурса формируются возможные URL-запросы.
    Если ответ 200 и в HTML содержится DOI или PDF — статья считается найденной.
    Возвращает словарь:
      - pirates: словарь {ресурс: True/False}
      - pirates_any: общий флаг (нашлась ли где-либо)
    """
    if not pirate_bases:
        return {}
    doi_q = quote_plus(doi)
    found_any = False
    details = {}

    for base in pirate_bases:
        ok = False
        candidates = []

        # формируем варианты URL в зависимости от структуры ресурса
        if base.endswith("=") or base.endswith("/"):
            candidates.append(base + doi_q)
        else:
            candidates.append(base + "/" + doi_q)
            candidates.append(base + "?q=" + doi_q)

        for u in candidates:
            try:
                r = requests.get(u, headers=HEADERS, timeout=REQUEST_TIMEOUT)
                if r.status_code == 200 and doi.lower() in r.text.lower():
                    ok = True
                    break
                if r.status_code == 200 and ".pdf" in r.text.lower():
                    ok = True
                    break
            except Exception:
                pass
        details[base] = ok
        if ok:
            found_any = True

    return {"pirates": details, "pirates_any": found_any}

def check_researchgate(doi):
    """
    Проверяет наличие статьи по DOI на ResearchGate.
    Возможные результаты:
      - "yes": статья точно найдена
      - "maybe": страница открылась, но DOI не найден в HTML
      - "unknown": ошибка или сайт недоступен
    """
    url = f"https://www.researchgate.net/search/publication?q={quote_plus(doi)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200 and doi.lower() in r.text.lower():
            return "yes"
        if r.status_code == 200:
            return "maybe"
    except Exception:
        pass
    return "unknown"
