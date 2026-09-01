"""Shared ICA REST client — the Tier B wiring for all five proposals.

Conventions verified against the SSIX3QJ Knowledge Center (May 2026); source of
truth is the live Swagger: https://servicesessentials.ibm.com/apis/docs/swagger-ui/index.html
(The bundled `ica-api` skill's host/path are stale — do not copy from it.)

Usage:
    python ica_client.py selftest                       # works with or without a key
    python ica_client.py assistants [--limit 10]
    python ica_client.py prompt --assistant <id> --q "..." [--collection <id>]

Env: ICA_API_KEY (required for live calls), ICA_REGION (optional: us, uki, remea,
     au, canada, japan, india, sg — defaults to the global host).
"""

import argparse
import json
import os
import sys
import time

import requests

GLOBAL_HOST = "https://servicesessentials.ibm.com"


def host() -> str:
    region = os.environ.get("ICA_REGION", "").strip().lower()
    return f"https://{region}.ica.ibm.com/ica" if region else GLOBAL_HOST


class ICAClient:
    def __init__(self, api_key: str = "", retries: int = 3):
        self.api_key = api_key or os.environ.get("ICA_API_KEY", "")
        self.retries = retries
        self.base = host()

    @property
    def ready(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _request(self, method: str, path: str, **kw):
        if not self.ready:
            raise RuntimeError(
                "ICA_API_KEY not set. Get one from ICA > Settings > My Settings > "
                "API Keys (shown once). Tier A paths work without it.")
        url = f"{self.base}{path}"
        last = None
        for attempt in range(1, self.retries + 1):
            try:
                r = requests.request(method, url, headers=self._headers(), timeout=120, **kw)
                if r.status_code in (429, 502, 503, 504):
                    raise requests.RequestException(f"retryable HTTP {r.status_code}")
                r.raise_for_status()
                return r.json()
            except requests.RequestException as exc:
                last = exc
                if attempt < self.retries:
                    wait = 2 ** attempt
                    print(f"  attempt {attempt} failed ({exc}); retrying in {wait}s", file=sys.stderr)
                    time.sleep(wait)
        raise RuntimeError(f"ICA call failed after {self.retries} attempts: {last}")

    # ---- endpoints ----

    def list_assistants(self, limit: int = 20) -> list:
        out = self._request("GET", f"/apis/v3/assistants?limit={limit}")
        return out.get("data", out) if isinstance(out, dict) else out

    def list_models(self) -> list:
        out = self._request("GET", "/apis/v3/models")
        return out.get("data", out) if isinstance(out, dict) else out

    def execute_prompt(self, assistant_id: str, prompt: str,
                       collection_id: str = "", system_prompt: str = "",
                       chat_id: str = "") -> dict:
        body = {"assistantId": assistant_id, "prompt": prompt}
        if collection_id: body["collectionId"] = collection_id
        if system_prompt: body["systemPrompt"] = system_prompt
        if chat_id: body["chatId"] = chat_id
        return self._request("POST", "/apis/v3/executePrompt", json=body)


def selftest() -> None:
    c = ICAClient()
    print(f"host: {c.base}")
    if not c.ready:
        print("ICA_API_KEY: not set — offline checks only.")
        try:
            c.list_assistants()
            print("FAIL: expected a helpful error without a key")
        except RuntimeError as e:
            print(f"no-key behavior OK: {str(e)[:80]}...")
        print("selftest PASS (offline). Set ICA_API_KEY and rerun for the live check.")
        return
    print("ICA_API_KEY: set — live check.")
    agents = c.list_assistants(limit=5)
    names = [a.get("name", a.get("id", "?")) for a in agents][:5]
    print(f"assistants reachable: {len(agents)} (first: {names})")
    print("selftest PASS (live).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    la = sub.add_parser("assistants"); la.add_argument("--limit", type=int, default=20)
    pr = sub.add_parser("prompt")
    pr.add_argument("--assistant", required=True); pr.add_argument("--q", required=True)
    pr.add_argument("--collection", default=""); pr.add_argument("--system", default="")
    a = ap.parse_args()
    if a.cmd == "selftest":
        selftest()
    elif a.cmd == "assistants":
        print(json.dumps(ICAClient().list_assistants(a.limit), indent=1, default=str)[:4000])
    elif a.cmd == "prompt":
        out = ICAClient().execute_prompt(a.assistant, a.q, a.collection, a.system)
        print(json.dumps(out, indent=1, default=str)[:4000])
