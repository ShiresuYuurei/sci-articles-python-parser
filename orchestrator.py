from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from typing import Dict, Any, List

from config import get_concurrency_settings
from cache_manager import load_doi_cache, save_doi_cache

def stage_collect_dois(issns: List, keywords: list, date_from: str,
                       date_to: str, rows: int) -> Dict[str, Any]:
    from crossref_client import collect_unique_by_doi

    print("=== Stage 1: Collecting works by ISSNs ===")
    dois_data = {}
    max_workers = get_concurrency_settings()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(collect_unique_by_doi, issn, keywords,
                            date_from, date_to, rows): issn
            for issn in issns
        }

        with tqdm(total=len(futures), ncols=100) as pbar:
            for future in as_completed(futures):
                doi_data = future.result()
                dois_data.update(doi_data)
                pbar.update(1)

    return dois_data

def stage_process_dois(dois_data: Dict[str, Any], pirate_urls: list,
                       check_rg: bool) -> List[Any]:

    print("=== Stage 2: Processing DOIs ===")
    results = []
    max_workers = get_concurrency_settings()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_doi_item, doi, raw_data,
                            pirate_urls, check_rg): doi
            for doi, raw_data in dois_data.items()
        }

        with tqdm(total=len(futures), ncols=100) as pbar:
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                pbar.update(1)

    return results

def process_single_doi_item(doi: str, raw_data: Any, pirate_urls: list,
                            check_rg: bool) -> Dict[str, Any]:
    """
    Обрабатывает один DOI: проверяет доступность на сайте издателя, ResearchGate и пиратских ресурсах,
    затем нормализует данные для сохранения

    :param doi: DOI статьи.
    :param raw_data: Сырые данные.
    :param pirate_urls: Список URL пиратских ресурсов.
    :param check_rg: Проверять ли ResearchGate.
    :return: Нормализованные данные.
    """
    from availability_checker import publisher_availability, check_pirates, check_researchgate
    from utils import normalize_item

    pub_av = publisher_availability(raw_data)
    pirates = check_pirates(doi, pirate_urls) if pirate_urls else {"pirates_any": False, "pirates": {}}
    rg = check_researchgate(doi) if check_rg else "not_checked"
    return normalize_item(doi, raw_data, pub_av, pirates, rg)

def process_dois(cfg: Dict[str, Any]) -> List[Any]:
    cache_path = cfg.get("doi_cache_path", "cached_dois.json")

    dois_data = load_doi_cache(cache_path)

    if not dois_data:
        dois_data = stage_collect_dois(
            cfg.get("issns", []),
            cfg.get("keywords", []),
            cfg.get("date_from"),
            cfg.get("date_to"),
            cfg.get("crossref_rows", 100)
        )
        save_doi_cache(dois_data, cache_path)

    print("Total unique DOIs found:", len(dois_data))

    results = stage_process_dois(
        dois_data,
        cfg.get("pirate_urls", []),
        cfg.get("check_researchgate", False)
    )

    return results