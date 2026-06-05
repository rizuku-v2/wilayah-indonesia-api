#!/usr/bin/env python3
"""
Validate generated API files.
Usage: python scripts/validate.py [--strict]
"""

import json
import sys
from pathlib import Path

ROOT    = Path(__file__).parent.parent
API_DIR = ROOT / "api"

OK   = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
WARN = "\033[93m!\033[0m"

errors   = []
warnings = []

def check(cond, msg_ok, msg_fail, fatal=False):
    if cond:
        print(f"  {OK} {msg_ok}")
    else:
        print(f"  {FAIL} {msg_fail}")
        if fatal:
            errors.append(msg_fail)
        else:
            warnings.append(msg_fail)
    return cond


def validate():
    print("\n  🔍  Validasi API Wilayah Indonesia\n")

    # ── provinces.json ─────────────────────────────────────────────
    print("  [provinces.json]")
    pf = API_DIR / "provinces.json"
    if not check(pf.exists(), "provinces.json ada", "provinces.json TIDAK ADA", fatal=True):
        return

    provinces = json.loads(pf.read_text())
    check(isinstance(provinces, list), f"Bentuk list ({len(provinces)} item)", "Bukan list")
    check(len(provinces) >= 34, f"{len(provinces)} provinsi (≥34 OK)", f"Hanya {len(provinces)} provinsi")
    check(len(provinces) >= 38, f"{len(provinces)} provinsi termasuk Papua baru", f"Papua baru mungkin belum ada ({len(provinces)}/38)")

    prov_codes = [p["code"] for p in provinces]
    check(all("code" in p and "name" in p for p in provinces),
          "Semua field code+name ada",
          "Ada provinsi tanpa field code/name")

    # ── regencies/ ─────────────────────────────────────────────────
    print("\n  [regencies/]")
    reg_dir = API_DIR / "regencies"
    reg_files = list(reg_dir.glob("*.json")) if reg_dir.exists() else []
    check(len(reg_files) > 0, f"{len(reg_files)} file kabupaten/kota", "Tidak ada file regencies")
    check(len(reg_files) >= len(prov_codes),
          f"Semua provinsi punya file regency",
          f"Ada provinsi tanpa data regency ({len(reg_files)}/{len(prov_codes)})")

    total_reg = 0
    reg_with_type = 0
    for f in reg_files:
        regs = json.loads(f.read_text())
        total_reg += len(regs)
        for r in regs:
            if "type" in r:
                reg_with_type += 1
    check(total_reg > 400, f"{total_reg:,} total kab/kota (>400 OK)", f"Hanya {total_reg} kab/kota")
    check(reg_with_type == total_reg,
          "Semua kab/kota punya field 'type'",
          f"{total_reg - reg_with_type} kab/kota tanpa field 'type'",
          fatal=False)

    # ── districts/ ─────────────────────────────────────────────────
    print("\n  [districts/]")
    dist_dir = API_DIR / "districts"
    dist_files = list(dist_dir.glob("*.json")) if dist_dir.exists() else []
    check(len(dist_files) > 0, f"{len(dist_files)} file kecamatan", "Tidak ada file districts")
    check(len(dist_files) >= total_reg,
          f"Semua kab/kota punya data kecamatan",
          f"Ada kab/kota tanpa data kecamatan ({len(dist_files)}/{total_reg})")

    total_dist = sum(len(json.loads(f.read_text())) for f in dist_files)
    check(total_dist > 5000, f"{total_dist:,} total kecamatan (>5000 OK)", f"Hanya {total_dist} kecamatan")

    # ── villages/ ──────────────────────────────────────────────────
    print("\n  [villages/]")
    vil_dir = API_DIR / "villages"
    vil_files = list(vil_dir.glob("*.json")) if vil_dir.exists() else []
    check(len(vil_files) > 0, f"{len(vil_files)} file desa/kelurahan", "Tidak ada file villages")

    total_vil   = 0
    with_postal = 0
    for f in vil_files[:200]:  # Sampling 200 file
        vils = json.loads(f.read_text())
        total_vil   += len(vils)
        with_postal += sum(1 for v in vils if "postal_code" in v)

    sample_pct = 100 * with_postal // max(1, total_vil)
    check(sample_pct >= 50,
          f"Kode pos coverage (sample): {sample_pct}%",
          f"Kode pos coverage rendah: {sample_pct}% (sample 200 file)",
          fatal=False)

    # Hitung total desa (semua file)
    total_all_vil = sum(len(json.loads(f.read_text())) for f in vil_files)
    check(total_all_vil > 70000,
          f"{total_all_vil:,} total desa/kelurahan (>70K OK)",
          f"Hanya {total_all_vil:,} desa/kelurahan")

    # ── search.json ────────────────────────────────────────────────
    print("\n  [search.json]")
    sf = API_DIR / "search.json"
    if sf.exists():
        search = json.loads(sf.read_text())
        check("provinces" in search and "regencies" in search,
              "search.json punya key provinces + regencies",
              "search.json format salah")
    else:
        warnings.append("search.json tidak ada")
        print(f"  {WARN} search.json tidak ada")

    # ── meta.json ─────────────────────────────────────────────────
    print("\n  [meta.json]")
    mf = API_DIR / "meta.json"
    if mf.exists():
        meta = json.loads(mf.read_text())
        check("generated_at" in meta, "meta.json valid", "meta.json format salah")
    else:
        warnings.append("meta.json tidak ada")
        print(f"  {WARN} meta.json tidak ada")

    # ── Ringkasan ──────────────────────────────────────────────────
    print(f"\n  {'─' * 40}")
    if errors:
        print(f"  ❌  {len(errors)} ERROR, {len(warnings)} warning")
        for e in errors:
            print(f"     • {e}")
        sys.exit(1)
    elif warnings:
        print(f"  ⚠️   OK dengan {len(warnings)} warning")
        for w in warnings:
            print(f"     • {w}")
    else:
        print(f"  ✅  Semua validasi lulus!")
    print()


if __name__ == "__main__":
    validate()
