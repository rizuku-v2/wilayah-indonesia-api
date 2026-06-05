#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║      🗺️  Wilayah Indonesia — Static API Generator v3.0             ║
║  Provinsi → Kabupaten/Kota → Kecamatan → Kelurahan/Desa + Kodepos  ║
╚══════════════════════════════════════════════════════════════════════╝

Sumber data (dengan fallback otomatis):
  1. cahyadsn/wilayah   — SQL dump lengkap (primary) [FIXED URL]
  2. kodewilayah/permendagri-72-2019 — CSV fallback
  3. sooluh/kodepos     — Kode Pos [UPDATED SOURCE]

Format kode wilayah (titik-separated dari sumber baru):
  11           → Provinsi
  11.01        → Kabupaten/Kota
  11.01.01     → Kecamatan
  11.01.01.2001 → Kelurahan/Desa

Output (kode tanpa titik, sesuai BPS):
  11       → 11
  11.01    → 1101
  11.01.01 → 110101
  11.01.01.2001 → 1101012001  (tanda baca stripped)

Usage:
  python scripts/generate.py
  python scripts/generate.py --force        # Re-download paksa
  python scripts/generate.py --clean        # Bersihkan output dulu
  python scripts/generate.py --no-kodepos   # Tanpa kode pos
  python scripts/generate.py --source csv   # Pakai fallback CSV
"""

import argparse
import csv
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════
# KONFIGURASI
# ═══════════════════════════════════════════════════════════════════════

ROOT     = Path(__file__).parent.parent
API_DIR  = ROOT / "api"
DATA_DIR = ROOT / "data"
CACHE    = ROOT / ".cache"

SOURCES = {
    # ── Primary SQL ──────────────────────────────────────────────────
    "sql": {
        "url":   "https://raw.githubusercontent.com/cahyadsn/wilayah/master/db/wilayah.sql",
        "cache": "wilayah.sql",
        "desc":  "cahyadsn/wilayah (SQL — Kepmendagri 2025)",
    },
    # ── CSV Fallback ──────────────────────────────────────────────────
    "csv": {
        "url":   "https://raw.githubusercontent.com/kodewilayah/permendagri-72-2019/main/dist/base.csv",
        "cache": "wilayah_base.csv",
        "desc":  "kodewilayah/permendagri-72-2019 (CSV)",
    },
    # ── Kode Pos ─────────────────────────────────────────────────────
    "kodepos": {
        "url":   "https://raw.githubusercontent.com/sooluh/kodepos/main/data/kodepos.json",
        "cache": "kodepos_sooluh.json",
        "desc":  "sooluh/kodepos",
    },
}

# ═══════════════════════════════════════════════════════════════════════
# UTILITAS
# ═══════════════════════════════════════════════════════════════════════

class C:
    RED    = '\033[91m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    BLUE   = '\033[94m'
    CYAN   = '\033[96m'
    BOLD   = '\033[1m'
    RESET  = '\033[0m'

def colored(text, *codes): return "".join(codes) + str(text) + C.RESET
def info(msg):  print(f"  {colored('→', C.CYAN)} {msg}")
def ok(msg):    print(f"  {colored('✓', C.GREEN)} {msg}")
def warn(msg):  print(f"  {colored('!', C.YELLOW)} {msg}", file=sys.stderr)
def err(msg):   print(f"  {colored('✗', C.RED)} {msg}", file=sys.stderr)
def step(t):    print(f"\n{colored(f'  ▶  {t}', C.BOLD + C.BLUE)}")
def bar(n, t):
    pct = int(50 * n / max(t, 1))
    return f"[{'█' * pct}{'░' * (50 - pct)}] {n:,}/{t:,}"

def download(url: str, cache_path: Path, force: bool = False) -> Optional[bytes]:
    """Download URL dengan caching. Kembalikan bytes atau None jika gagal."""
    if not force and cache_path.exists() and cache_path.stat().st_size > 0:
        info(f"Cache: {cache_path.name} ({cache_path.stat().st_size:,} bytes)")
        return cache_path.read_bytes()

    info(f"Fetching: {url[:80]}{'…' if len(url) > 80 else ''}")
    t0 = time.time()
    try:
        req = Request(url, headers={
            "User-Agent": "wilayah-indonesia-api/3.0 (github.com)",
        })
        with urlopen(req, timeout=180) as resp:
            data = resp.read()

        elapsed = time.time() - t0
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(data)
        ok(f"Downloaded {len(data):,} bytes ({elapsed:.1f}s)")
        return data

    except HTTPError as e:
        err(f"HTTP {e.code}: {url}")
    except URLError as e:
        err(f"Network error: {e.reason}")
    except Exception as e:
        err(f"Error: {e}")
    return None

def write_json(path: Path, data, pretty: bool = False) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if pretty:
            json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    return path.stat().st_size

def dotted_to_flat(kode: str) -> str:
    """
    Konversi kode bertitik ke kode flat BPS.
    '11.01'        → '1101'
    '11.01.01'     → '110101'
    '11.01.01.2001'→ '1101012001'
    """
    return kode.replace(".", "")

def norm(s: str) -> str:
    s = s.upper().strip()
    for pfx in ["KELURAHAN ", "DESA ", "KEL. ", "DS. ",
                "KECAMATAN ", "KEC. ", "KABUPATEN ", "KAB. ",
                "KOTA ADMINISTRASI ", "KOTA ", "KABUPATEN ADMINISTRASI "]:
        if s.startswith(pfx):
            s = s[len(pfx):]
    s = re.sub(r"['\-\./]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

# ═══════════════════════════════════════════════════════════════════════
# PARSING SQL  (format BARU: kode bertitik)
# ═══════════════════════════════════════════════════════════════════════

def parse_sql(raw: bytes) -> List[Tuple[str, str]]:
    """
    Parse SQL dump cahyadsn/wilayah.
    Format baru menggunakan kode bertitik:
      INSERT INTO wilayah (kode, nama) VALUES
      ('11','Aceh'),
      ('11.01','Kabupaten Aceh Selatan'),
      ('11.01.01','Bakongan'),
      ('11.01.01.2001','Keude Bakongan');

    Kembalikan list (kode_flat, nama).
    """
    sql = raw.decode("utf-8", errors="replace")
    records: List[Tuple[str, str]] = []

    # Match setiap pasangan nilai dalam blok VALUES
    # Format: ('11.01.01.2001','Nama Wilayah')
    # Perhatikan: nama bisa mengandung tanda petik ganda ('') sebagai escape
    val_re = re.compile(
        r"\('([0-9]+(?:\.[0-9]+){0,3})'\s*,\s*'((?:[^'\\]|''|\\.)*)'\s*\)"
    )

    for m in val_re.finditer(sql):
        kode_dot = m.group(1).strip()
        nama     = m.group(2).strip().replace("''", "'")  # unescape single-quote
        if kode_dot and nama:
            records.append((dotted_to_flat(kode_dot), nama))

    return records

# ═══════════════════════════════════════════════════════════════════════
# PARSING CSV  (fallback)
# ═══════════════════════════════════════════════════════════════════════

def parse_csv(raw: bytes) -> List[Tuple[str, str]]:
    """
    Parse CSV kodewilayah/permendagri-72-2019.
    Format: 11,ACEH  /  11.01,KAB. ACEH SELATAN  /  ...
    """
    import io
    records: List[Tuple[str, str]] = []
    text = raw.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    for row in reader:
        if len(row) < 2:
            continue
        kode_dot = row[0].strip()
        nama     = row[1].strip()
        # Validasi format kode
        if re.match(r"^[0-9]+(?:\.[0-9]+){0,3}$", kode_dot) and nama:
            records.append((dotted_to_flat(kode_dot), nama))
    return records

# ═══════════════════════════════════════════════════════════════════════
# KLASIFIKASI HIERARKI  (berdasarkan jumlah digit kode flat)
# ═══════════════════════════════════════════════════════════════════════

def classify(records: List[Tuple[str, str]]) -> Dict:
    """
    Klasifikasikan records berdasarkan panjang kode flat:
      2  digit  → Provinsi
      4  digit  → Kabupaten / Kota
      6  digit  → Kecamatan
      10 digit  → Kelurahan / Desa (atau ≥7 untuk fleksibilitas)
    """
    provinces: List[dict]       = []
    regencies: Dict[str, list]  = {}
    districts: Dict[str, list]  = {}
    villages:  Dict[str, list]  = {}

    seen = set()  # deduplikasi

    for kode_flat, nama in sorted(records, key=lambda x: (len(x[0]), x[0])):
        if kode_flat in seen:
            continue
        seen.add(kode_flat)

        n = len(kode_flat)

        if n == 2:
            provinces.append({"code": kode_flat, "name": nama.upper()})

        elif n == 4:
            prov = kode_flat[:2]
            upper = nama.upper()
            if upper.startswith("KOTA ") or upper.startswith("KOTA ADMINISTRASI "):
                type_ = "kota"
            elif "ADMINISTRASI" in upper:
                type_ = "kabupaten_administrasi"
            else:
                type_ = "kabupaten"

            regencies.setdefault(prov, []).append({
                "code":          kode_flat,
                "province_code": prov,
                "name":          nama.upper(),
                "type":          type_,
            })

        elif n == 6:
            reg = kode_flat[:4]
            districts.setdefault(reg, []).append({
                "code":         kode_flat,
                "regency_code": reg,
                "name":         nama.upper(),
            })

        elif n >= 7:
            dist = kode_flat[:6]
            villages.setdefault(dist, []).append({
                "code":          kode_flat,
                "district_code": dist,
                "name":          nama.upper(),
            })

    return dict(
        provinces=provinces,
        regencies=regencies,
        districts=districts,
        villages=villages,
    )

# ═══════════════════════════════════════════════════════════════════════
# KODE POS  (sooluh/kodepos format)
# ═══════════════════════════════════════════════════════════════════════

def load_kodepos(force: bool = False) -> Dict[str, str]:
    """
    Muat data kode pos dari sooluh/kodepos.
    Format item: {code, village, district, regency, province, ...}
    Return index: {key → kode_pos}
    """
    src = SOURCES["kodepos"]
    raw = download(src["url"], CACHE / src["cache"], force=force)
    if not raw or len(raw) < 100:
        return {}

    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        err("Gagal parse kode pos JSON")
        return {}

    index: Dict[str, str] = {}

    for item in items:
        # code bisa berupa integer atau string
        kode = str(item.get("code", "")).strip().zfill(5)
        if not kode or kode == "00000":
            continue

        kel  = norm(str(item.get("village",  "")))
        kec  = norm(str(item.get("district", "")))
        kab  = norm(str(item.get("regency",  "")))
        prov = norm(str(item.get("province", "")))

        keys = [
            f"{kel}|{kec}|{kab}|{prov}",
            f"{kel}|{kec}|{kab}",
            f"{kel}|{kec}",
        ]
        for k in keys:
            if k and k not in index:
                index[k] = kode
        if kel:
            index.setdefault(kel, kode)

    ok(f"Loaded {len(index):,} kode pos entries dari sooluh/kodepos")
    return index

def enrich_kodepos(data: Dict, kodepos_idx: Dict[str, str]) -> Tuple[int, int]:
    reg_name:  Dict[str, str] = {}
    dist_name: Dict[str, str] = {}
    prov_name: Dict[str, str] = {}

    for p in data["provinces"]:
        prov_name[p["code"]] = norm(p["name"])

    for reg_list in data["regencies"].values():
        for r in reg_list:
            reg_name[r["code"]] = norm(r["name"])

    for dist_list in data["districts"].values():
        for d in dist_list:
            dist_name[d["code"]] = norm(d["name"])

    matched = total = 0

    for dist_code, vil_list in data["villages"].items():
        kec  = dist_name.get(dist_code, "")
        reg  = dist_code[:4]
        kab  = reg_name.get(reg, "")
        prov = prov_name.get(reg[:2], "")

        for vil in vil_list:
            total += 1
            kel = norm(vil["name"])

            postal = (
                kodepos_idx.get(f"{kel}|{kec}|{kab}|{prov}")
                or kodepos_idx.get(f"{kel}|{kec}|{kab}")
                or kodepos_idx.get(f"{kel}|{kec}")
                or kodepos_idx.get(kel)
            )

            if postal:
                vil["postal_code"] = postal
                matched += 1

    return matched, total

# ═══════════════════════════════════════════════════════════════════════
# GENERATE OUTPUT
# ═══════════════════════════════════════════════════════════════════════

def generate(data: Dict, out: Path) -> Dict:
    total_bytes = 0
    stats = {}

    size = write_json(out / "provinces.json", data["provinces"])
    total_bytes += size
    stats["provinces"] = len(data["provinces"])

    reg_dir = out / "regencies"
    reg_count = 0
    for pcode, regs in data["regencies"].items():
        if regs:
            total_bytes += write_json(reg_dir / f"{pcode}.json", regs)
            reg_count += len(regs)
    stats["regencies"] = reg_count

    dist_dir = out / "districts"
    dist_count = 0
    for rcode, dists in data["districts"].items():
        if dists:
            total_bytes += write_json(dist_dir / f"{rcode}.json", dists)
            dist_count += len(dists)
    stats["districts"] = dist_count

    vil_dir = out / "villages"
    vil_count = 0
    for dcode, vils in data["villages"].items():
        if vils:
            total_bytes += write_json(vil_dir / f"{dcode}.json", vils)
            vil_count += len(vils)
    stats["villages"] = vil_count

    search = {
        "provinces": data["provinces"],
        "regencies": [r for rl in data["regencies"].values() for r in rl],
    }
    write_json(out / "search.json", search)

    import datetime
    meta = {
        "generated_at":     int(time.time()),
        "generated_at_iso": datetime.datetime.utcnow().isoformat() + "Z",
        "version":          "3.0",
        "source":           "cahyadsn/wilayah + sooluh/kodepos",
        "license":          "Open Data / MIT",
        "total": {
            "provinces":  stats["provinces"],
            "regencies":  stats["regencies"],
            "districts":  stats["districts"],
            "villages":   stats["villages"],
        },
        "total_size_bytes": total_bytes,
        "endpoints": {
            "provinces":  "/api/provinces.json",
            "regencies":  "/api/regencies/{province_code}.json",
            "districts":  "/api/districts/{regency_code}.json",
            "villages":   "/api/villages/{district_code}.json",
            "search":     "/api/search.json",
        },
    }
    write_json(out / "meta.json", meta, pretty=True)

    stats["total_bytes"] = total_bytes
    return stats

# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def parse_args():
    p = argparse.ArgumentParser(
        description="Generate Wilayah Indonesia Static API v3.0",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument("--force",      action="store_true", help="Re-download paksa")
    p.add_argument("--clean",      action="store_true", help="Hapus direktori api/")
    p.add_argument("--no-kodepos", action="store_true", help="Skip kode pos")
    p.add_argument("--source",     choices=["sql", "csv"], default="sql",
                   help="Sumber data (default: sql)")
    p.add_argument("--dry-run",    action="store_true", help="Parse tanpa tulis file")
    return p.parse_args()


def main():
    args = parse_args()
    t_start = time.time()

    print(colored("\n  🗺️  Wilayah Indonesia — Static API Generator v3.0", C.BOLD + C.CYAN))
    print(colored("  " + "═" * 54, C.CYAN))
    print(f"  Source  : {colored(args.source.upper(), C.BOLD)}")
    print(f"  Kodepos : {colored('YA', C.GREEN) if not args.no_kodepos else colored('SKIP', C.YELLOW)}")

    CACHE.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if args.clean and API_DIR.exists():
        step("Membersihkan direktori output")
        shutil.rmtree(API_DIR)
        ok(f"Dihapus: {API_DIR}")

    API_DIR.mkdir(parents=True, exist_ok=True)

    # ── [1] Ambil data wilayah ────────────────────────────────────────
    step("[1/4] Mengambil data wilayah")
    records: List[Tuple[str, str]] = []

    if args.source == "csv":
        src = SOURCES["csv"]
        info(f"Sumber: {src['desc']}")
        raw = download(src["url"], CACHE / src["cache"], force=args.force)
        if raw:
            records = parse_csv(raw)
            ok(f"Parsed {len(records):,} records dari CSV")
    else:
        src = SOURCES["sql"]
        info(f"Sumber: {src['desc']}")
        raw = download(src["url"], CACHE / src["cache"], force=args.force)
        if raw:
            info("Parsing SQL dump…")
            records = parse_sql(raw)
            ok(f"Parsed {len(records):,} records dari SQL")
        else:
            warn("SQL gagal → mencoba fallback CSV…")
            src2 = SOURCES["csv"]
            raw2 = download(src2["url"], CACHE / src2["cache"], force=args.force)
            if raw2:
                records = parse_csv(raw2)
                ok(f"Parsed {len(records):,} records dari CSV fallback")

    if not records:
        err("Tidak ada data! Periksa koneksi internet.")
        err("Coba: python scripts/generate.py --source csv")
        sys.exit(1)

    # ── [2] Klasifikasi ───────────────────────────────────────────────
    step("[2/4] Klasifikasi level wilayah")
    data = classify(records)

    prov_n  = len(data["provinces"])
    reg_n   = sum(len(v) for v in data["regencies"].values())
    dist_n  = sum(len(v) for v in data["districts"].values())
    vil_n   = sum(len(v) for v in data["villages"].values())

    info(f"Provinsi:        {prov_n:>6,}")
    info(f"Kab/Kota:        {reg_n:>6,}")
    info(f"Kecamatan:       {dist_n:>6,}")
    info(f"Kelurahan/Desa:  {vil_n:>6,}")

    if prov_n < 34:
        warn(f"Hanya {prov_n} provinsi — mungkin ada masalah parsing")

    # ── [3] Kode Pos ──────────────────────────────────────────────────
    if not args.no_kodepos and vil_n > 0:
        step("[3/4] Mengambil & mencocokkan kode pos")
        kodepos_idx = load_kodepos(force=args.force)
        if kodepos_idx:
            matched, total = enrich_kodepos(data, kodepos_idx)
            pct = 100 * matched // max(1, total)
            ok(f"Kode pos: {matched:,}/{total:,} cocok ({pct}%)")
            if pct < 30:
                warn(f"Match rate rendah ({pct}%)")
        else:
            warn("Kode pos tidak tersedia — lanjut tanpa kode pos")
    else:
        step("[3/4] Lewati kode pos")

    # ── [4] Tulis file ────────────────────────────────────────────────
    if args.dry_run:
        step("[4/4] Dry run — tidak ada file yang ditulis")
        ok("Selesai (dry run)")
        return

    step(f"[4/4] Menulis file ke {API_DIR}/")
    stats = generate(data, API_DIR)

    elapsed = time.time() - t_start
    mb = stats["total_bytes"] / 1_000_000

    print(f"\n  {colored('═' * 54, C.GREEN)}")
    print(f"  {colored('✅  Selesai dalam {:.1f} detik'.format(elapsed), C.BOLD + C.GREEN)}")
    print(f"  {colored('═' * 54, C.GREEN)}")
    print(f"  Provinsi:        {stats['provinces']:>7,}")
    print(f"  Kab/Kota:        {stats['regencies']:>7,}")
    print(f"  Kecamatan:       {stats['districts']:>7,}")
    print(f"  Kelurahan/Desa:  {stats['villages']:>7,}")
    print(f"  Total ukuran:    {mb:>6.1f} MB")
    print(f"  Output:          {API_DIR}/")
    print()


if __name__ == "__main__":
    main()
