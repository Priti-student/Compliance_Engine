"""Print extracted declarations + top violations for an inspection token."""
import sys
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8001"

with httpx.Client(base_url=BASE, timeout=30) as c:
    r = c.post("/api/auth/login", data={"username": "officer", "password": "Officer@123"})
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    token = sys.argv[1]
    d = c.get(f"/api/inspections/{token}", headers=h).json()

    print("PRODUCT:", (d.get("product") or {}).get("generic_name"))
    print("STATUS:", d["compliance_status"], "| stats:", d["stats"])
    print("\nEXTRACTED DECLARATIONS:")
    for dec in d["declarations"]:
        print(f"  {dec['field_name']:<34} {str(dec['value'])[:70]}  ({dec['method']})")
    print("\nVIOLATIONS (rule / status / severity / reason):")
    for v in d["violations"]:
        print(f"  {v['rule_id']:<7} {v['status']:<15} {v['severity']:<6} {v['reason'][:90]}")
    print("\nFONT METRICS (zone / px / mm / contrast):")
    for m in d["font_metrics"]:
        mm = round(m["char_height_mm_median"], 3) if m["calibrated"] else "-"
        print(f"  {m['zone_type']:<30} {m['char_height_px_median']:>7.1f}  {mm}  {m['contrast_ratio']:.2f}")