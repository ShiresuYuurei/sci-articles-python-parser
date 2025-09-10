import json
import os
from typing import Dict, Any

def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file {config_path} not found. Please create it.")

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_concurrency_settings() -> int:
    cpu_count = os.cpu_count() or 4
    return min(12, cpu_count * 3)

def save_results(results: list, cfg: Dict[str, Any]) -> None:
    from exporter import save
    outjson = cfg.get("output", {}).get("json", "output.json")
    outexcel = cfg.get("output", {}).get("excel", "output.xlsx")
    save(results, outjson, outexcel)
    print(f"Saved: {outjson}, {outexcel}")