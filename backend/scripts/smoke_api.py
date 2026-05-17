"""Quick API smoke test against a running Scanlyr backend."""

from __future__ import annotations

import sys
import uuid

import httpx

BASE = "http://127.0.0.1:8000/api/v1"


def main() -> int:
    suffix = uuid.uuid4().hex[:8]
    email = f"smoke-{suffix}@example.com"
    password = "SmokeTest1A!"

    c = httpx.Client(base_url=BASE, timeout=60.0)
    failed = 0

    def check(name: str, r: httpx.Response, ok: tuple[int, ...] = (200, 201)) -> bool:
        nonlocal failed
        good = r.status_code in ok
        tag = "PASS" if good else "FAIL"
        print(f"{tag} {name}: {r.status_code}")
        if not good:
            failed += 1
            print(f"  {r.text[:300]}")
        return good

    r = httpx.get("http://127.0.0.1:8000/health", timeout=10.0)
    check("GET /health", r)

    r = c.post(
        "/auth/register",
        json={"organization_name": f"Smoke Org {suffix}", "email": email, "password": password},
    )
    if not check("POST /auth/register", r):
        return 1

    token = r.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    check("GET /auth/me", c.get("/auth/me", headers=headers))
    check(
        "POST /scan",
        c.post(
            "/scan",
            headers=headers,
            json={"input_text": "My SSN is 123-45-6789 and I use ChatGPT", "content_type": "prompt"},
        ),
    )
    check("GET /scan/history", c.get("/scan/history?limit=10", headers=headers))
    check("GET /scan/analytics", c.get("/scan/analytics", headers=headers))

    det = c.get("/detections?limit=10", headers=headers)
    check("GET /detections", det)
    det_total = det.json().get("total", 0) if det.status_code == 200 else 0

    check("GET /integrations/microsoft/status", c.get("/integrations/microsoft/status", headers=headers))
    check("GET /reports", c.get("/reports?limit=10", headers=headers))

    gen = c.post("/reports/generate", headers=headers, json={})
    if gen.status_code in (200, 201):
        check("POST /reports/generate", gen)
        rep = gen.json()
        rid = rep.get("id")
        if rid and rep.get("status") == "ready":
            dl = c.get(f"/reports/{rid}/download", headers=headers)
            check("GET /reports/{id}/download", dl)
            if dl.status_code == 200:
                print(f"  PDF size: {len(dl.content)} bytes")
    else:
        print(f"WARN POST /reports/generate: {gen.status_code} {gen.text[:200]}")
        failed += 1

    print("---")
    print(f"Smoke user: {email}")
    print(f"Detections total: {det_total}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
