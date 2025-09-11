import json
import os
from typing import Dict, Any, List
from decorators import stage_logger
from utils import open_folder_prompt

@stage_logger("Stage 1: Loading configuration")
def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file {config_path} not found. Please create it.")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Config file {config_path} is corrupted. Error: {e}") from e
    except IOError as e:
        raise IOError(f"Error reading cofig file {config_path}. Error: {e}") from e

def get_concurrency_settings() -> int:
    cpu_count: int = os.cpu_count() or 4
    return min(12, cpu_count * 3)

@stage_logger("Stage 4: Saving results")
def save_results(results: List[Dict[str, Any]], cfg: Dict[str, Any]) -> None:
    from exporter import save
    outjson: str = cfg.get("output", {}).get("json", "output.json")
    outexcel: str = cfg.get("output", {}).get("excel", "output.xlsx")

    try:
        save(results, outjson, outexcel)
        open_folder_prompt(cfg)
    except Exception as e:
        print(f"Error saving results: {e}")
        raise

