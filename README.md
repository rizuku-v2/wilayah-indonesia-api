# 🗺️ API Wilayah Indonesia (Static)

**Static API** data wilayah administratif Indonesia yang di-host di GitHub Pages.

Bebas downtime. Bebas rate limit. Bebas biaya server. Selalu tersedia.

---

## ✨ Fitur

- **38 Provinsi** termasuk 4 provinsi Papua baru (2022)
- **500+ Kabupaten/Kota** dengan penanda `kabupaten` atau `kota`
- **7.000+ Kecamatan**
- **80.000+ Kelurahan/Desa** dengan **Kode Pos**
- **Auto-update** bulanan via GitHub Actions
- **Zero dependency** — pure Python stdlib
- Response **CORS-friendly** (GitHub Pages)
- Format **JSON compact** untuk performa

---

## 🚀 Quick Start

### 1. Fork & Clone

```bash
git clone https://github.com/USERNAME/wilayah-indonesia-api.git
cd wilayah-indonesia-api
```

### 2. Generate Data Pertama Kali

```bash
python scripts/generate.py
```

Atau paksa re-download:

```bash
python scripts/generate.py --force --clean
```

### 3. Validasi

```bash
python scripts/validate.py
```

### 4. Deploy ke GitHub Pages

1. Push ke GitHub
2. Buka **Settings → Pages → Source → Deploy from a branch**
3. Pilih branch `main`, folder `/ (root)`
4. Klik Save

API langsung tersedia di:
```
https://USERNAME.github.io/wilayah-indonesia-api/api/provinces.json
```

### 5. (Opsional) Custom Domain

Buat file `CNAME` berisi domain kamu, misal:
```
api.wilayah.id
```

---

## 📡 Endpoint

Base URL: `https://USERNAME.github.io/wilayah-indonesia-api`

| Endpoint | Deskripsi |
|----------|-----------|
| `GET /api/provinces.json` | Semua provinsi |
| `GET /api/regencies/{kode_provinsi}.json` | Kab/kota dalam provinsi |
| `GET /api/districts/{kode_kabupaten}.json` | Kecamatan dalam kab/kota |
| `GET /api/villages/{kode_kecamatan}.json` | Kelurahan/desa + kode pos |
| `GET /api/search.json` | Index provinsi + kab/kota (untuk search) |
| `GET /api/meta.json` | Metadata & statistik |

---

## 📄 Format Response

### `provinces.json`
```json
[
  { "code": "32", "name": "JAWA BARAT" },
  { "code": "33", "name": "JAWA TENGAH" }
]
```

### `regencies/32.json`
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
  }
]
```

### `districts/3201.json`
```json
[
  {
    "code": "320101",
    "regency_code": "3201",
    "name": "NANGGUNG"
  }
]
```

### `villages/320101.json`
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

### `search.json`
```json
{
  "provinces": [ ... ],
  "regencies":  [ ... ]
}
```

### `meta.json`
```json
{
  "generated_at": 1700000000,
  "generated_at_iso": "2024-11-14T10:00:00Z",
  "version": "2.0",
  "total": {
    "provinces": 38,
    "regencies": 514,
    "districts": 7285,
    "villages": 83762
  }
}
```

---

## 💡 Contoh Penggunaan

### JavaScript (Fetch API)

```javascript
const BASE = 'https://USERNAME.github.io/wilayah-indonesia-api/api';

// Ambil semua provinsi
const provinces = await fetch(`${BASE}/provinces.json`).then(r => r.json());

// Ambil kab/kota berdasarkan kode provinsi
const regencies = await fetch(`${BASE}/regencies/32.json`).then(r => r.json());

// Ambil kecamatan
const districts = await fetch(`${BASE}/districts/3201.json`).then(r => r.json());

// Ambil kelurahan + kode pos
const villages = await fetch(`${BASE}/villages/320101.json`).then(r => r.json());

// Cari desa tertentu dengan kode pos
const found = villages.find(v => v.name === 'MALASARI');
console.log(found?.postal_code); // "16650"
```

### React / Next.js

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

### PHP

```php
$base = 'https://USERNAME.github.io/wilayah-indonesia-api/api';

// Ambil provinsi
$provinces = json_decode(file_get_contents("$base/provinces.json"), true);

// Ambil kab/kota provinsi Jawa Barat (kode 32)
$regencies = json_decode(file_get_contents("$base/regencies/32.json"), true);
```

---

## ⚙️ Generate Options

```
python scripts/generate.py [OPTIONS]

Options:
  --force        Re-download paksa (bypass cache)
  --clean        Hapus direktori api/ sebelum generate
  --no-kodepos   Tanpa enrichment kode pos (lebih cepat)
  --source       Pilih sumber: 'sql' (default) atau 'emsifa' (fallback)
  --dry-run      Parse saja tanpa tulis file
```

---

## 🔄 Auto-Update

GitHub Actions berjalan otomatis:

- **Bulanan**: Tanggal 1 setiap bulan pukul 02:00 UTC
- **Manual**: Via tab Actions → "Run workflow"
- **Push**: Saat ada perubahan di `scripts/`

Untuk trigger manual dengan opsi:

1. Buka tab **Actions**
2. Klik **🗺️ Generate Wilayah API**
3. Klik **Run workflow**
4. Pilih opsi (source, force, dll)

---

## 📦 Sumber Data

| Sumber | Digunakan untuk |
|--------|----------------|
| [cahyadsn/wilayah_db](https://github.com/cahyadsn/wilayah_db) | Data wilayah utama (SQL) |
| [emsifa/api-wilayah-indonesia](https://github.com/emsifa/api-wilayah-indonesia) | Fallback wilayah (JSON) |
| [ibnux/data-indonesia](https://github.com/ibnux/data-indonesia) | Kode Pos |

Data berdasarkan kode BPS/Kemendagri resmi Indonesia.

---

## 📝 Lisensi

Data wilayah Indonesia adalah data publik dari BPS dan Kemendagri.
Kode generator: [MIT License](LICENSE)
