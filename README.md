<a href="https://s.id/standwithpalestine"><img alt="I stand with Palestine" src="https://cdn.jsdelivr.net/gh/Safouene1/support-palestine-banner@master/banner-project.svg" width="100%" /></a>

# 🗺️ API Wilayah Indonesia (Static) v3.0

> 🇮🇩 [Bahasa Indonesia](#bahasa-indonesia) | 🇬🇧 [English](#english)

---

## Bahasa Indonesia

**Static API** data wilayah administratif Indonesia yang di-host di GitHub Pages.

> Bebas downtime. Bebas rate limit. Bebas biaya server. Selalu tersedia.

---

### ✨ Fitur

- **38 Provinsi** — termasuk 4 provinsi Papua baru (2022)
- **500+ Kabupaten/Kota** — dengan penanda tipe `kabupaten`, `kota`, atau `kabupaten_administrasi`
- **7.000+ Kecamatan**
- **80.000+ Kelurahan/Desa** — dilengkapi **Kode Pos**
- **Auto-update bulanan** via GitHub Actions
- **Zero dependency** — murni Python standard library
- **CORS-friendly** — kompatibel langsung dari browser
- **JSON compact** — format ringan untuk performa optimal

---

### 🚀 Cara Penggunaan

#### 1. Fork & Clone

```bash
git clone https://github.com/USERNAME/wilayah-indonesia-api.git
cd wilayah-indonesia-api
```

#### 2. Generate Data Pertama Kali

```bash
python scripts/generate.py
```

Atau paksa re-download (bypass cache):

```bash
python scripts/generate.py --force --clean
```

#### 3. Validasi Data

```bash
python scripts/validate.py
```

#### 4. Deploy ke GitHub Pages

1. Push ke GitHub
2. Buka **Settings → Pages → Source → Deploy from a branch**
3. Pilih branch `main`, folder `/ (root)`
4. Klik **Save**

API langsung tersedia di:

```
https://USERNAME.github.io/wilayah-indonesia-api/api/provinces.json
```

#### 5. (Opsional) Custom Domain

Buat file `CNAME` berisi domain Anda, contoh:

```
api.wilayah.id
```

---

### 📡 Daftar Endpoint

Base URL: `https://USERNAME.github.io/wilayah-indonesia-api`

| Endpoint | Deskripsi |
|---|---|
| `GET /api/provinces.json` | Semua provinsi |
| `GET /api/regencies/{kode_provinsi}.json` | Kabupaten/kota dalam provinsi |
| `GET /api/districts/{kode_kabupaten}.json` | Kecamatan dalam kabupaten/kota |
| `GET /api/villages/{kode_kecamatan}.json` | Kelurahan/desa beserta kode pos |
| `GET /api/search.json` | Indeks provinsi + kabupaten/kota (untuk pencarian) |
| `GET /api/meta.json` | Metadata & statistik keseluruhan |

---

### 📄 Format Response

#### `provinces.json`

```json
[
  { "code": "32", "name": "JAWA BARAT" },
  { "code": "33", "name": "JAWA TENGAH" }
]
```

#### `regencies/32.json`

```json
[
  {
    "code": "3201",
    "province_code": "32",
    "name": "KABUPATEN BOGOR",
    "type": "kabupaten"
  },
  {
    "code": "3271",
    "province_code": "32",
    "name": "KOTA BOGOR",
    "type": "kota"
  },
  {
    "code": "3172",
    "province_code": "31",
    "name": "KOTA ADMINISTRASI JAKARTA SELATAN",
    "type": "kabupaten_administrasi"
  }
]
```

#### `districts/3201.json`

```json
[
  {
    "code": "320101",
    "regency_code": "3201",
    "name": "NANGGUNG"
  }
]
```

#### `villages/320101.json`

```json
[
  {
    "code": "3201010001",
    "district_code": "320101",
    "name": "MALASARI",
    "postal_code": "16650"
  }
]
```

#### `search.json`

```json
{
  "provinces": [ "..." ],
  "regencies":  [ "..." ]
}
```

#### `meta.json`

```json
{
  "generated_at": 1700000000,
  "generated_at_iso": "2024-11-14T10:00:00Z",
  "version": "3.0",
  "source": "cahyadsn/wilayah + sooluh/kodepos",
  "license": "Open Data / MIT",
  "total": {
    "provinces": 38,
    "regencies": 514,
    "districts": 7285,
    "villages": 83762
  },
  "total_size_bytes": 12345678,
  "endpoints": {
    "provinces":  "/api/provinces.json",
    "regencies":  "/api/regencies/{province_code}.json",
    "districts":  "/api/districts/{regency_code}.json",
    "villages":   "/api/villages/{district_code}.json",
    "search":     "/api/search.json"
  }
}
```

---

### 💡 Contoh Penggunaan

#### JavaScript (Fetch API)

```javascript
const BASE = 'https://USERNAME.github.io/wilayah-indonesia-api/api';

// Ambil semua provinsi
const provinces = await fetch(`${BASE}/provinces.json`).then(r => r.json());

// Ambil kabupaten/kota berdasarkan kode provinsi
const regencies = await fetch(`${BASE}/regencies/32.json`).then(r => r.json());

// Ambil kecamatan
const districts = await fetch(`${BASE}/districts/3201.json`).then(r => r.json());

// Ambil kelurahan + kode pos
const villages = await fetch(`${BASE}/villages/320101.json`).then(r => r.json());

// Cari desa tertentu
const found = villages.find(v => v.name === 'MALASARI');
console.log(found?.postal_code); // "16650"
```

#### React / Next.js

```tsx
import useSWR from 'swr';

const BASE = process.env.NEXT_PUBLIC_WILAYAH_API;
const fetcher = (url: string) => fetch(url).then(r => r.json());

function ProvinceSelect() {
  const { data: provinces } = useSWR(`${BASE}/provinces.json`, fetcher);
  return (
    <select>
      {provinces?.map(p => (
        <option key={p.code} value={p.code}>{p.name}</option>
      ))}
    </select>
  );
}
```

#### PHP

```php
$base = 'https://USERNAME.github.io/wilayah-indonesia-api/api';

// Ambil semua provinsi
$provinces = json_decode(file_get_contents("$base/provinces.json"), true);

// Ambil kabupaten/kota Jawa Barat (kode 32)
$regencies = json_decode(file_get_contents("$base/regencies/32.json"), true);
```

---

### ⚙️ Opsi Generate

```bash
python scripts/generate.py [OPTIONS]

Opsi:
  --force        Re-download paksa (bypass cache)
  --clean        Hapus direktori api/ sebelum generate
  --no-kodepos   Tanpa enrichment kode pos (lebih cepat)
  --source       Pilih sumber: 'sql' (default) atau 'csv' (fallback CSV)
  --dry-run      Parse saja tanpa menulis file
```

---

### 🔄 Auto-Update

GitHub Actions berjalan otomatis pada jadwal berikut:

- **Bulanan** — Setiap tanggal 1, pukul 02:00 UTC
- **Manual** — Melalui tab **Actions → Run workflow**
- **Push** — Saat ada perubahan di direktori `scripts/`

Untuk trigger manual:

1. Buka tab **Actions**
2. Klik **🗺️ Generate Wilayah API**
3. Klik **Run workflow**
4. Pilih opsi yang diinginkan (source, force, dll.)

---

### 📦 Sumber Data

| Sumber | Digunakan untuk |
|---|---|
| [cahyadsn/wilayah](https://github.com/cahyadsn/wilayah) | Data wilayah utama (SQL — Kepmendagri 2025) |
| [kodewilayah/permendagri-72-2019](https://github.com/kodewilayah/permendagri-72-2019) | Fallback wilayah (CSV) |
| [sooluh/kodepos](https://github.com/sooluh/kodepos) | Kode Pos |

Data mengacu pada kode resmi BPS (Badan Pusat Statistik) dan Kemendagri (Kementerian Dalam Negeri) Republik Indonesia.

---

### 📝 Lisensi

Data wilayah Indonesia merupakan data publik dari BPS dan Kemendagri.
Kode generator: [MIT License](./LICENSE)

---
---

## English

**Static API** for Indonesian administrative region data, hosted on GitHub Pages.

> No downtime. No rate limits. No server costs. Always available.

---

### ✨ Features

- **38 Provinces** — including 4 new Papua provinces (2022)
- **500+ Regencies/Cities** — labeled with type `kabupaten` (regency), `kota` (city), or `kabupaten_administrasi` (administrative regency)
- **7,000+ Districts**
- **80,000+ Sub-districts/Villages** — with **Postal Codes**
- **Monthly auto-update** via GitHub Actions
- **Zero dependency** — pure Python standard library
- **CORS-friendly** — usable directly from the browser
- **Compact JSON** — lightweight format for optimal performance

---

### 🚀 Getting Started

#### 1. Fork & Clone

```bash
git clone https://github.com/USERNAME/wilayah-indonesia-api.git
cd wilayah-indonesia-api
```

#### 2. Generate Data for the First Time

```bash
python scripts/generate.py
```

Or force a re-download (bypass cache):

```bash
python scripts/generate.py --force --clean
```

#### 3. Validate Data

```bash
python scripts/validate.py
```

#### 4. Deploy to GitHub Pages

1. Push to GitHub
2. Go to **Settings → Pages → Source → Deploy from a branch**
3. Select branch `main`, folder `/ (root)`
4. Click **Save**

The API will be available at:

```
https://USERNAME.github.io/wilayah-indonesia-api/api/provinces.json
```

#### 5. (Optional) Custom Domain

Create a `CNAME` file with your domain, for example:

```
api.wilayah.id
```

---

### 📡 Endpoints

Base URL: `https://USERNAME.github.io/wilayah-indonesia-api`

| Endpoint | Description |
|---|---|
| `GET /api/provinces.json` | All provinces |
| `GET /api/regencies/{province_code}.json` | Regencies/cities within a province |
| `GET /api/districts/{regency_code}.json` | Districts within a regency/city |
| `GET /api/villages/{district_code}.json` | Villages/sub-districts with postal codes |
| `GET /api/search.json` | Province + regency index (for search) |
| `GET /api/meta.json` | Metadata & overall statistics |

---

### 📄 Response Format

#### `provinces.json`

```json
[
  { "code": "32", "name": "JAWA BARAT" },
  { "code": "33", "name": "JAWA TENGAH" }
]
```

#### `regencies/32.json`

```json
[
  {
    "code": "3201",
    "province_code": "32",
    "name": "KABUPATEN BOGOR",
    "type": "kabupaten"
  },
  {
    "code": "3271",
    "province_code": "32",
    "name": "KOTA BOGOR",
    "type": "kota"
  },
  {
    "code": "3172",
    "province_code": "31",
    "name": "KOTA ADMINISTRASI JAKARTA SELATAN",
    "type": "kabupaten_administrasi"
  }
]
```

#### `districts/3201.json`

```json
[
  {
    "code": "320101",
    "regency_code": "3201",
    "name": "NANGGUNG"
  }
]
```

#### `villages/320101.json`

```json
[
  {
    "code": "3201010001",
    "district_code": "320101",
    "name": "MALASARI",
    "postal_code": "16650"
  }
]
```

#### `search.json`

```json
{
  "provinces": [ "..." ],
  "regencies":  [ "..." ]
}
```

#### `meta.json`

```json
{
  "generated_at": 1700000000,
  "generated_at_iso": "2024-11-14T10:00:00Z",
  "version": "3.0",
  "source": "cahyadsn/wilayah + sooluh/kodepos",
  "license": "Open Data / MIT",
  "total": {
    "provinces": 38,
    "regencies": 514,
    "districts": 7285,
    "villages": 83762
  },
  "total_size_bytes": 12345678,
  "endpoints": {
    "provinces":  "/api/provinces.json",
    "regencies":  "/api/regencies/{province_code}.json",
    "districts":  "/api/districts/{regency_code}.json",
    "villages":   "/api/villages/{district_code}.json",
    "search":     "/api/search.json"
  }
}
```

---

### 💡 Usage Examples

#### JavaScript (Fetch API)

```javascript
const BASE = 'https://USERNAME.github.io/wilayah-indonesia-api/api';

// Get all provinces
const provinces = await fetch(`${BASE}/provinces.json`).then(r => r.json());

// Get regencies by province code
const regencies = await fetch(`${BASE}/regencies/32.json`).then(r => r.json());

// Get districts
const districts = await fetch(`${BASE}/districts/3201.json`).then(r => r.json());

// Get villages with postal codes
const villages = await fetch(`${BASE}/villages/320101.json`).then(r => r.json());

// Find a specific village
const found = villages.find(v => v.name === 'MALASARI');
console.log(found?.postal_code); // "16650"
```

#### React / Next.js

```tsx
import useSWR from 'swr';

const BASE = process.env.NEXT_PUBLIC_WILAYAH_API;
const fetcher = (url: string) => fetch(url).then(r => r.json());

function ProvinceSelect() {
  const { data: provinces } = useSWR(`${BASE}/provinces.json`, fetcher);
  return (
    <select>
      {provinces?.map(p => (
        <option key={p.code} value={p.code}>{p.name}</option>
      ))}
    </select>
  );
}
```

#### PHP

```php
$base = 'https://USERNAME.github.io/wilayah-indonesia-api/api';

// Get all provinces
$provinces = json_decode(file_get_contents("$base/provinces.json"), true);

// Get regencies in West Java (code 32)
$regencies = json_decode(file_get_contents("$base/regencies/32.json"), true);
```

---

### ⚙️ Generate Options

```bash
python scripts/generate.py [OPTIONS]

Options:
  --force        Force re-download (bypass cache)
  --clean        Remove api/ directory before generating
  --no-kodepos   Skip postal code enrichment (faster)
  --source       Choose source: 'sql' (default) or 'csv' (CSV fallback)
  --dry-run      Parse only, without writing files
```

---

### 🔄 Auto-Update

GitHub Actions runs automatically on the following schedule:

- **Monthly** — On the 1st of every month at 02:00 UTC
- **Manual** — Via **Actions → Run workflow**
- **On push** — When changes are made inside the `scripts/` directory

To trigger manually:

1. Open the **Actions** tab
2. Click **🗺️ Generate Wilayah API**
3. Click **Run workflow**
4. Select desired options (source, force, etc.)

---

### 📦 Data Sources

| Source | Used for |
|---|---|
| [cahyadsn/wilayah](https://github.com/cahyadsn/wilayah) | Primary region data (SQL — Kepmendagri 2025) |
| [kodewilayah/permendagri-72-2019](https://github.com/kodewilayah/permendagri-72-2019) | Region fallback (CSV) |
| [sooluh/kodepos](https://github.com/sooluh/kodepos) | Postal Codes |

Data is based on official codes from BPS (Statistics Indonesia) and Kemendagri (Ministry of Home Affairs) of the Republic of Indonesia.

---

### 📝 License

Indonesian region data is public data from BPS and Kemendagri.
Generator code: [MIT License](./LICENSE)
