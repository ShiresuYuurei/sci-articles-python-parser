def normalize_item(doi, raw_data, pub_av, pirate_res, rg):
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
    title = raw_data.get("title", [""])[0] if raw_data.get("title") else ""

    # Список авторов
    authors = []
    for a in raw_data.get("author", []):
        g = a.get("given","").strip()
        f = a.get("family","").strip()
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
    citations = raw_data.get("is-referenced-by-count", 0)

    # Ссылка на страницу статьи
    url = raw_data.get("URL", "")

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
        "link": url,
        "available_on_site": "yes" if pub_av.get("publisher_pdf") or pub_av.get("open_access") else "no",
        "researchgate": rg_status,
        "pirates": pirates_yesno
    }