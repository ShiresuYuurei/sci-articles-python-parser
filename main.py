import json, os
from crossref_client import collect_unique_by_doi
from availability_checker import publisher_availability, check_pirates, check_researchgate
from exporter import normalize_item, save
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

DOI_CACHE_FILE = "cached_dois.json"

def process_single_issn(issn, keywords, date_from, date_to, rows):
    """
    Обрабатывает один ISSN: собирает все уникальные DOI статей по заданным параметрам.

    :param issn: ISSN журнала
    :param keywords: Список ключевых слов для поиска
    :param date_from: Дата начала поиска в формате 'YYYY-MM-DD'
    :param date_to: Дата окончания поиска
    :param rows: Максимальное количество результатов для одного ISSN
    :return: ISSN и словарь {doi: raw_data}
    """
    doi_data = collect_unique_by_doi([issn], keywords, date_from, date_to, rows=rows)
    return issn, doi_data

def process_single_doi(doi_raw_tuple, pirate_urls, check_rg, metrics):
    """
    Обрабатывает один DOI: проверяет доступность на сайте издателя, ResearchGate и пиратских ресурсах,
    затем нормализует данные для сохранения

    :param doi_raw_tuple: Кортеж (doi, raw_data)
    :param pirate_urls: Список URL пиратских ресурсов
    :param check_rg: Проверять ли ResearchGate
    :param metrics: Метрики журнала (impact factor (IF), квартиль), если есть.
    :return: Кортеж (normalized_item, doi) - нормализованные данные и DOI
    """
    doi, raw = doi_raw_tuple
    pub_av = publisher_availability(raw)
    pirates = check_pirates(doi, pirate_urls) if pirate_urls else {"pirates_any": False, "pirates": {}}
    rg = check_researchgate(doi) if check_rg else "not_checked"
    norm = normalize_item(doi, raw, pub_av, pirates, rg, metrics)
    return norm, doi

def main(cfg_path="config.json"):
    """
    Основной блок программы.
    1. Загружает конфигурацию
    2. Сбор DOI по ISSN с параллельной обработкой и прогресс-баром.
    3. Обработка каждого DOI (доступность, пиратские ресурсы, ResearchGate) с параллельной обработкой.
    4. Сохраняет результаты в JSON и Excel.

    :param cfg_path: Путь к конфигурации парсера
    :return: None
    """
    if not os.path.exists(cfg_path):
        print("Create config.json (see template).")
        return

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    issns = cfg.get("issns", [])
    keywords = cfg.get("keywords", [])
    date_from = cfg.get("date_from")
    date_to = cfg.get("date_to")
    rows = cfg.get("crossref_rows", 100)
    pirate_urls = cfg.get("pirate_urls", [])
    check_rg = cfg.get("check_researchgate", False)

    by_doi = {}

    # Настройки числа потоков для ThreadPoolExecutor в зависимости от CPU
    cpu_count = os.cpu_count() or 4
    max_workers = min(12, cpu_count * 3)  # I/O-bound задачи: несколько потоков на ядро

    # ========================
    # Этап 1: Сбор DOI
    # ========================
    print("=== Stage 1: Collecting works by ISSNs ===")

    if os.path.exists(DOI_CACHE_FILE):
        # Загружаем кэшированные DOI, если файл существует
        print(f"Loading cached DOIs from {DOI_CACHE_FILE}")
        with open(DOI_CACHE_FILE, "r", encoding="utf-8") as f:
            by_doi = json.load(f)
    else:
        # Параллельная обработка ISSN
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_single_issn, issn, keywords, date_from, date_to, rows):
                           issn for issn in issns}
            with tqdm(total=len(futures), ncols=100) as pbar_issn:
                for future in as_completed(futures):
                    issn, doi_data = future.result()
                    by_doi.update(doi_data)

                    # Показываем текущий ISSN в прогресс-баре
                    pbar_issn.set_postfix_str(f"Current ISSN: {issn}")
                    pbar_issn.update(1)

        # Сохраняем кэш DOI для ускорения тестов
        with open(DOI_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(by_doi, f, ensure_ascii=False, indent=2)
        print(f"Saved cached DOIs to {DOI_CACHE_FILE}")

    print("Total unique DOIs found:", len(by_doi))

    # Метрики журналов (в данной реализации не используются)
    metrics = {}
    results = []

    # ========================
    # Этап 2: Обработка DOI
    # ========================
    print("=== Stage 2: Processing DOIs ===")

    # Параллельная обработка DOI
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single_doi, (doi, raw), pirate_urls, check_rg, metrics):
                       doi for doi, raw in by_doi.items()}

        with tqdm(total=len(futures), ncols=100) as pbar_doi:
            for future in as_completed(futures):
                norm, doi = future.result()
                results.append(norm)

                # Показываем текущий DOI в прогресс-баре
                pbar_doi.set_postfix_str(f"Current DOI: {doi}")
                pbar_doi.update(1)

    # ========================
    # Этап 3: Сохранение результатов
    # ========================
    outjson = cfg.get("output", {}).get("json")
    outexcel = cfg.get("output", {}).get("excel")
    save(results, outjson, outexcel)
    print("Saved:", outjson, outexcel)
    print("Total records:", len(results))

if __name__ == "__main__":
    main()