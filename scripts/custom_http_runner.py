#!/usr/bin/env python3
"""Custom HTTP runner for GH Actions egress (additive; used by custom_http_check.yml).

Reads a JSON spec file with {"method","url","headers","body"} and performs one
request with requests, then writes result.json and prints compact JSON.
"""
import json, sys, time

import requests


def main():
    spec_path = sys.argv[1] if len(sys.argv) > 1 else "spec.json"
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)
    method = str(spec.get("method", "GET")).upper()
    url = spec["url"]
    headers = spec.get("headers") or {}
    body = spec.get("body")
    result = {
        "method": method,
        "url": url,
        "headers_sent": {k: v for k, v in headers.items()},
    }
    start = time.perf_counter()
    try:
        resp = requests.request(
            method, url, headers=headers, data=body if body not in (None, "") else None,
            timeout=30, allow_redirects=True, verify=False,
        )
        result["status_code"] = resp.status_code
        result["headers"] = {k: v for k, v in resp.headers.items()}
        result["body"] = resp.text[:200000]
        result["redirect_history"] = [h.url for h in resp.history]
        result["final_url"] = resp.url
        result["elapsed_ms"] = int((time.perf_counter() - start) * 1000)
    except Exception as e:  # noqa: BLE001
        result["error"] = f"{type(e).__name__}: {e}"
        result["status_code"] = 0
        result["elapsed_ms"] = int((time.perf_counter() - start) * 1000)
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    print(json.dumps({"status": result.get("status_code"), "method": method,
                      "url": url, "error": result.get("error"),
                      "body_len": len(result.get("body") or "")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
