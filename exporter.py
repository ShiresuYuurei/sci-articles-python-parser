import json, pandas as pd
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment
from openpyxl import load_workbook

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