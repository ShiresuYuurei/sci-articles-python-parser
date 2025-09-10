import json
import os
from typing import Dict, Any

def load_doi_cache(cache_path: str) -> Dict[str, Any]:
    if not os.path.exists(cache_path):
        return {}

    print(f"Loading cached DOIs from {cache_path}")
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Warning: Cache file {cache_path} is corrupted. Starting fresh. Error: {e}")
        return {}

def save_doi_cache(doi_data: Dict[str, Any], cache_path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(cache_path)), exist_ok=True)

    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(doi_data, f, ensure_ascii=False, indent=2)
        print(f"Saved cached DOIs to {cache_path}")
    except IOError as e:
        print(f"Error: Could not save cache to {cache_path}. Error: {e}")