import os.path
import subprocess
from typing import Dict, Any, List

def normalize_item(doi: str, raw_data: Dict[str, Any],
                   pub_av: Dict[str, Any], pirate_res: Dict[str, Any],
                   rg: str) -> Dict[str, Any]:
    """
    Приведение «сырых» данных о статье к единому формату для сохранения.

    :param doi: Идентификатор статьи
    :param raw_data: Исходные данные из CrossRef
    :param pub_av: Доступность статьи у издателя
    :param pirate_res: Результаты проверки на пиратских ресурсах
    :param rg: Статус наличия статьи на ResearchGate
    :return: Словарь с единообразными полями (год публикации, авторы, название статьи и др.)
    """
    # Заголовок
    title: str = raw_data.get("title", [""])[0] if raw_data.get("title") else ""

    # Список авторов
    authors = []
    for a in raw_data.get("author", []):
        g: str = a.get("given","").strip()
        f: str = a.get("family","").strip()
        authors.append((g + " " + f).strip())

    # Определение года публикации
    year = None
    for k in ("published", "published-online", "issued", "created"):
        v = raw_data.get(k)
        if v and isinstance(v, dict):
            dp = v.get("date-parts")
            if dp and len(dp) > 0 and len(dp[0]) > 0:
                year = dp[0][0]
                break

    # Количество цитирований
    citations: int = raw_data.get("reference-count", 0)

    # Ссылка на страницу статьи
    url: str = raw_data.get("URL", "")

    # Проверка пиратских ресурсов
    pirates_yesno = "yes" if pirate_res.get("pirates_any") else "no"

    # Проверка ResearchGate
    rg_status = "no"
    if rg == "yes":
        rg_status = "yes"
    elif rg == "unknown":
        rg_status = "maybe"

    return {
        "year": year,
        "authors": "; ".join(authors),
        "title": title,
        "doi": doi,
        "citations": citations,
        "link": url,
        "available_on_site": "yes" if pub_av.get("publisher_pdf") else "no",
        "researchgate": rg_status,
        "pirates": pirates_yesno
    }

def open_folder_prompt(cfg: Dict[str, Any]) -> None:
    """Функция для запроса открытия папки с результатом"""
    outjson = cfg.get("output", {}).get("json", "")
    outexcel = cfg.get("output", {}).get("excel", "")
    try:
        response = input("Open folder with results? (y/n): ").strip().lower()
        if response in ('y', 'yes', 'д', 'да'):
            file_path = outjson or outexcel
            if file_path:
                folder_path = os.path.dirname(os.path.abspath(file_path) or os.getcwd())
                open_folder(folder_path)
            else:
                print("No output files specified in config.")
        else:
            print(f"Saved {outjson}, {outexcel}")
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled by user.")

def open_folder(folder_path: str) -> None:
    """Открывает папку в файловом менеджере системы"""
    try:
        if os.name == 'nt':
            os.startfile(folder_path)
        elif os.name == 'posix':
            if os.uname().sysname == "Darwin":
                subprocess.run(['open', folder_path], check=True)
            else:
                subprocess.run(['xdg-open', folder_path], check=True)
    except Exception as e:
        print(f"Could not open folder: {e}")
