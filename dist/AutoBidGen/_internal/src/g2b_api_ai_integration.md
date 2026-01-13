# g2b_api — AI Integration Summary

This file documents the public functionality of `src/g2b_api.py` so another AI can immediately implement or call equivalent behavior.

**Module purpose**: Lookup product names from a 10-digit 세부품명번호 (item code) using:
- Remote API: 조달청 ThngListInfoService (getPrdctClsfcNoUnit10Info)
- Local mapping: `PRODUCT_MAPPING`
- Category inference: `get_category_name` from `src.product_mapping`

**Dependencies**:
- `requests` for HTTP calls
- `src.config.settings` (expects `G2B_SERVICE_KEY`)
- `src.product_mapping.PRODUCT_MAPPING` (dict) and `get_category_name()`

**Public functions and signatures**:

- `get_product_name_from_api(item_code: str) -> Optional[str]`
  - Calls the ThngListInfoService `getPrdctClsfcNoUnit10Info` operation.
  - Requires `settings.G2B_SERVICE_KEY` to be set; returns None if missing.
  - Validates `item_code` length == 10.
  - Parses JSON response; prefers exact 10-digit match, otherwise first result.
  - On success stores mapping into `PRODUCT_MAPPING[item_code]` and returns product name.
  - Handles HTTP errors, timeouts, and returns `None` on failure.

- `get_product_name_from_mapping(item_code: str) -> Optional[str]`
  - Returns `PRODUCT_MAPPING.get(item_code)` (local cache/fallback).

- `infer_product_name(item_code: str) -> str`
  - If `len(item_code) != 10`, returns `Product ({item_code})`.
  - Otherwise returns `{category} ({item_code})` where `category = get_category_name(item_code)`.

- `get_product_name(item_code: str) -> Optional[str]`
  - High-level lookup that tries, in order:
    1. `get_product_name_from_api`
    2. `get_product_name_from_mapping`
    3. `get_category_name` (inferred)
  - Validates input length; logs warnings on invalid format.

- `get_product_names(item_codes: List[str], max_workers: int = 3) -> Dict[str, Optional[str]]`
  - Concurrently resolves multiple codes using `ThreadPoolExecutor` and `get_product_name`.
  - Returns a mapping `code -> name_or_None`.
  - On individual lookup failures falls back to `infer_product_name`.

**Behavior notes for implementing AI-facing version**:
- Respect API key presence and return None / warnings when missing.
- Use timeout (~15s) for HTTP calls.
- Prefer exact 10-digit match; if not found, use best-effort first item.
- Threaded lookups for batch queries; default `max_workers=3`.
- Update local mapping cache when API returns a product name.

---

## Ready-to-paste prompt for another AI

Below is a prompt you can paste to an LLM to implement this module or to replicate its behavior in another language/runtime.

"Implement a module that provides functions to lookup product names by a 10-digit item code. The module must implement these functions with the same signatures and semantics provided. Key requirements:
- `get_product_name_from_api(item_code)` should call the ThngListInfoService `getPrdctClsfcNoUnit10Info` endpoint (base URL `https://apis.data.go.kr/1230000/ao/ThngListInfoService`) with `serviceKey` from configuration. Use JSON responses, 15s timeout, and handle HTTP 403 explicitly.
- `get_product_name_from_mapping(item_code)` reads from a provided `PRODUCT_MAPPING` dict.
- `infer_product_name(item_code)` returns a human-readable fallback using `get_category_name(item_code)`.
- `get_product_name(item_code)` tries API -> mapping -> inference in that order and stores API results into `PRODUCT_MAPPING`.
- `get_product_names(item_codes, max_workers=3)` should implement concurrent resolution and return a dict mapping codes to names, falling back to inference on errors.

Also include logging/debug prints similar to the original for visibility. Provide small examples showing single and batch lookups and sample expected outputs."

---

## Example usage (Python)

```py
from src.g2b_api import get_product_name, get_product_names

print(get_product_name("4111331501"))
print(get_product_names(["4111331501", "1234567890"]))
```

Expected behavior: returns product name strings when available, otherwise inferred category names or `None` depending on lookup stage and configuration.

---

## Implementation checklist for the AI
- [ ] Honor `G2B_SERVICE_KEY` from configuration.
- [ ] Use timeout and handle JSON parsing errors.
- [ ] Match exact 10-digit codes when possible.
- [ ] Update local mapping cache when API returns a name.
- [ ] Provide a batch resolver with concurrency and error fallbacks.


