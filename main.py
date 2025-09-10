import config
from orchestrator import process_dois

def main(cfg_path="config.json"):
    # Этап 1: Загрузка конфигурации
    cfg = config.load_config(cfg_path)

    # Этап 2: Обработка DOIs
    results = process_dois(cfg)

    # Этап 3: Сохранение результатов
    config.save_results(results, cfg)

    print(f"Done. Total records: {len(results)}")

if __name__ == "__main__":
    main()