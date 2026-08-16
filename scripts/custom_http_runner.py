#!/usr/bin/env python3
"""Custom HTTP runner for GH Actions egress (additive; used by custom_http_check.yml).

Reads a JSON spec file: either a single request {"method","url","headers","body"}
or an array of requests. Performs each with requests, sleeping >=3.3s between
requests. Writes result.json (single) / results-<n>.json (array) and prints
compact status lines.
"""
import json, sys, time

import requests

MIN_GAP = 3.3


def one_request(spec):
    method = str(spec.get("method", "GET")).upper()
    url = spec["url"]
    headers = spec.get("headers") or {}
    body = spec.get("body")
    out = {"method": method, "url": url, "headers_sent": dict(headers)}
    start = time.perf_counter()
    try:
        resp = requests.request(
            method, url, headers=headers, data=body if body not in (None, "") else None,
            timeout=30, allow_redirects=True, verify=False,
        )
        out["status_code"] = resp.status_code
        out["headers"] = {k: v for k, v in resp.headers.items()}
        out["body"] = resp.text[:200000]
        out["redirect_history"] = [h.url for h in resp.history]
        out["final_url"] = resp.url
        out["elapsed_ms"] = int((time.perf_counter() - start) * 1000)
    except Exception as e:  # noqa: BLE001
        out["error"] = f"{type(e).__name__}: {e}"
        out["status_code"] = 0
        out["elapsed_ms"] = int((time.perf_counter() - start) * 1000)
    return out


def main():
    spec_path = sys.argv[1] if len(sys.argv) > 1 else "spec.json"
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)
    requests_spec = spec if isinstance(spec, list) else [spec]
    results = []
    for i, rs in enumerate(requests_spec):
        if i > 0:
            time.sleep(MIN_GAP)
        r = one_request(rs)
        results.append(r)
        print(json.dumps({"status": r.get("status_code"), "method": r.get("method"),
                          "url": r.get("url"), "error": r.get("error"),
                          "body_len": len(r.get("body") or "")}, ensure_ascii=False))
    if len(results) == 1:
        with open("result.json", "w", encoding="utf-8") as f:
            json.dump(results[0], f, ensure_ascii=False)
    else:
        for i, r in enumerate(results):
            with open(f"results-{i}.json", "w", encoding="utf-8") as f:
                json.dump(r, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
