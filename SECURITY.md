# Security Policy

Bootcamp Agent adalah framework agen AI open-source yang dapat mengeksekusi
kode (bash, python). Secara default berjalan di host langsung; mode `sandbox`
di config.toml memberikan lapisan pengaman tambahan.

## Versi yang Didukung

| Versi  | Didukung          |
|--------|-------------------|
| latest | ✅ Patch & update |
| older  | ❌ Tidak          |

Kami hanya mendukung versi terbaru di branch `main`.

## Melaporkan Kerentanan

**Jangan buka issue publik** untuk kerentanan keamanan.

Kirim laporan privat ke email maintainer atau gunakan GitHub
[Private Vulnerability Reporting](https://github.com/Celebez/Bootcamp-Agent/security/advisories/new):

- Email: security@bootcamp.web.id (contoh — sesuaikan jika perlu)
- Sertakan: deskripsi kerentanan, langkah reproduksi, dampak, dan saran perbaikan.

Kami berjanji:
1. Balasan dalam 72 jam.
2. Investigasi rahasia tanpa mention publik.
3. Kredit untuk reporter (jika bersedia) setelah patch rilis.

## Sandbox & Mode Aman

Aktifkan sandbox di `config/config.toml`:

```toml
[sandbox]
mode = "enforce"      # off | warn | enforce
timeout = 300
allow_private_net = false
```

- `off`  — tidak ada pengecekan (default).
- `warn` — catat pelanggaran tapi jalankan.
- `enforce` — tolak eksekusi yang melanggar aturan.

## Bot Production Checklist

Sebelum menjalankan bot Telegram/Discord di publik:

```bash
export OML_PROD=1
export ALLOWED_TELEGRAM_USERS="123456789"     # ID Telegram user
export ALLOWED_DISCORD_GUILDS="987654321"     # ID guild Discord
```

`OML_PROD=1` + allow-list kosong → bot **tolak jalan**.

## Tanggung Jawab

Bootcamp Agent adalah alat bantu. Pengguna bertanggung jawab atas:
- Konten yang diproses/dihasilkan oleh agen.
- Kepatuhan terhadap hukum & ToS platform terkait.
- Tidak menggunakan untuk aktivitas ilegal.
