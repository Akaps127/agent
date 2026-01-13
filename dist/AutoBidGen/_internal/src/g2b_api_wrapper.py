"""
Lightweight wrapper to expose `src.g2b_api` behavior in a JSON-friendly way
for other AIs or services to call programmatically.

Provides:
- `g2b_lookup_single(item_code)` -> dict with keys: code, name, source
- `g2b_lookup_batch(item_codes, max_workers=3)` -> dict code->result dict

This wrapper avoids changing original module logic; it only adapts outputs.
"""
from typing import List, Dict, Optional

from src import g2b_api


def _result_dict(code: str, name: Optional[str], source: str) -> Dict:
    return {
        "code": code,
        "name": name,
        "source": source,
    }


def g2b_lookup_single(item_code: str) -> Dict:
    """Lookup one code and return a structured dict.

    source: 'api' | 'mapping' | 'inferred' | 'unknown'
    """
    # try API first
    api_name = g2b_api.get_product_name_from_api(item_code)
    if api_name:
        return _result_dict(item_code, api_name, "api")

    mapped = g2b_api.get_product_name_from_mapping(item_code)
    if mapped:
        return _result_dict(item_code, mapped, "mapping")

    # fallback inference
    inferred = g2b_api.infer_product_name(item_code)
    return _result_dict(item_code, inferred, "inferred")


def g2b_lookup_batch(item_codes: List[str], max_workers: int = 3) -> Dict[str, Dict]:
    """Batch lookup returning a map of code -> result dict.

    Uses `get_product_names` under the hood to respect the original concurrency behavior.
    """
    raw = g2b_api.get_product_names(item_codes, max_workers=max_workers)
    out: Dict[str, Dict] = {}
    for code, name in raw.items():
        if name is None:
            # None from API indicates failure to resolve; fallback to inference
            name = g2b_api.infer_product_name(code)
            source = "inferred"
        else:
            # try to guess source: if in PRODUCT_MAPPING then 'mapping' else 'api'
            if code in getattr(g2b_api, "PRODUCT_MAPPING", {}):
                # assume mapping was updated or contained result
                source = "mapping_or_api"
            else:
                source = "api_or_mapping"
        out[code] = _result_dict(code, name, source)
    return out


if __name__ == "__main__":
    examples = ["4111331501", "0000000000"]
    print("Single:")
    print(g2b_lookup_single(examples[0]))
    print("Batch:")
    print(g2b_lookup_batch(examples))
