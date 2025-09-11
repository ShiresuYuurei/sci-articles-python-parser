import config
from orchestrator import process_dois

def main(cfg_path="config.json"):
    # Этап 1: Загрузка конфигурации
    cfg = config.load_config(cfg_path)

    # Этапы 2 и 3: Обработка DOIs
    results = process_dois(cfg)

    # Этап 4: Сохранение результатов
    config.save_results(results, cfg)

if __name__ == "__main__":
    main()