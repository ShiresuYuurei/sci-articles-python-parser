import json, pandas as pd
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment
from openpyxl import load_workbook

def normalize_item(doi, raw_item, pub_av, pirate_res, rg, metrics_map):
    """
    Приведение «сырых» данных о статье к единому формату для сохранения.

    :param doi: Идентификатор статьи
    :param raw_item: Исходные данные из CrossRef
    :param pub_av: Доступность статьи у издателя
    :param pirate_res: Результаты проверки на пиратских ресурсах
    :param rg: Статус наличия статьи на ResearchGate
    :param metrics_map: Словарь с метриками журналов (IF, Quartile)
    :return: Словарь с единообразными полями (год публикации, авторы, название статьи и др.)
    """
    # Заголовок
    title = raw_item.get("title", [""])[0] if raw_item.get("title") else ""

    # Список авторов
    authors = []
    for a in raw_item.get("author", []):
        g = a.get("given","").strip()
        f = a.get("family","").strip()
        authors.append((g + " " + f).strip())

    # Определение года публикации
    year = None
    for k in ("published", "published-online", "issued", "created"):
        v = raw_item.get(k)
        if v and isinstance(v, dict):
            dp = v.get("date-parts")
            if dp and len(dp) > 0 and len(dp[0]) > 0:
                year = dp[0][0]
                break

    # Количество цитирований
    citations = raw_item.get("is-referenced-by-count", 0)

    # Ссылка на страницу статьи
    url = raw_item.get("URL", "")

    # ISSN журнала (для поиска метрик)
    issns = raw_item.get("ISSN", [])
    impact = None
    quartile = None
    for issn in issns:
        if issn in metrics_map:
            impact = metrics_map[issn].get("impact_factor")
            quartile = metrics_map[issn].get("quartile")
            break

    # Проверка пиратских ресурсов
    pirates_yesno = "yes" if pirate_res.get("pirates_any") else "no"

    # Проверка ResearchGate
    rg_status = "no"
    if rg == "yes":
        rg_status = "yes"
    elif rg in ("maybe", "unknown"):
        rg_status = "maybe"

    return {
        "year": year,
        "authors": "; ".join(authors),
        "title": title,
        "doi": doi,
        "citations": citations,
        "impact_factor": impact,
        "quartile": quartile or "no",
        "link": url,
        "available_on_site": "yes" if pub_av.get("publisher_pdf") or pub_av.get("open_access") else "no",
        "researchgate": rg_status,
        "pirates": pirates_yesno
    }

def save(results_list, out_json=None, out_excel=None):
    """
    Сохраняет результаты работы парсера:
      - в JSON-файл (если указан out_json),
      - в Excel (если указан out_excel).

    В Excel добавляется оформление:
      - фиксированные ширины столбцов,
      - выравнивание текста по центру,
      - перенос по словам для длинных ячеек.
    """
    # Сохранение в JSON
    if out_json:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(results_list, f, ensure_ascii=False, indent=2)

    # Сохранение в Excel
    if out_excel:
        df = pd.DataFrame(results_list)
        df.to_excel(out_excel, index=False)

        # Ширина столбцов (заранее подобранные значения для читаемости)
        col_widths = {
            "year": 6,
            "authors": 40,
            "title": 60,
            "doi": 30,
            "citations": 11,
            "impact_factor": 15,
            "quartile": 10,
            "link": 50,
            "available_on_site": 19,
            "researchgate": 14,
            "pirates": 9
        }

        wb = load_workbook(out_excel)
        ws = wb.active

        for i, col in enumerate(ws.columns, start=1):
            col_letter = get_column_letter(i)
            header = ws.cell(row=1, column=i).value

            # Берём ширину из словаря или дефолтное значение
            width = col_widths.get(header, 15)
            ws.column_dimensions[col_letter].width = width

            # Выравнивание и перенос слов для всех ячеек
            for cell in col:
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        wb.save(out_excel)