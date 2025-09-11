import config
from orchestrator import stage_process_dois
from cache_manager import load_doi_cache
from typing import Dict, Any
import asyncio
from itertools import islice

async def test(sample_size=10):
    cfg = config.load_config()

    cache_path: str = cfg.get("doi_cache_path", "cached_dois.json")
    dois_data: Dict[str, Any] = load_doi_cache(cache_path)

    subset = dict(islice(dois_data.items(), sample_size))

    results = stage_process_dois(
        subset,
        cfg.get("pirate_urls", []),
        cfg.get("check_researchgate", False)
    )

    config.save_results(results, cfg)

if __name__ == "__main__":
    asyncio.run(test(sample_size=10))

