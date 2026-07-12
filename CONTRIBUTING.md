# Kontribusi ke Bootcamp Agent

Terima kasih sudah tertarik untuk berkontribusi. Bootcamp Agent adalah
kerangka agen AI sumber terbuka; setiap bantuan — dari koreksi ejaan
sampai modul baru — sangat kami apresiasi.

## Kode etik
- Bersikap sopan dan terbuka terhadap kontributor lain.
- Beri konteks yang cukup saat bertanya di issue/PR.
- Tidak menyertakan API key, token, atau data pribadi apa pun.

## Alur kontribusi
1. **Fork** repositori ini lalu buat branch dari `main`.
2. Ikuti gaya penulisan kode di bawah; jalankan `ruff check .` sebelum commit.
3. Tambahkan/ubah **test** untuk perilaku baru. `pytest tests/` harus lulus.
4. Buka **Pull Request** dengan deskripsi singkat: masalah → solusi → efek samping.
5. Tunggu review; kami mungkin minta revisi kecil sebelum merge.

## Pelaporan bug
Gunakan template di issue. Sertakan:
- Perintah tepat yang dijalankan (`python main.py ...`).
- Output / pesan galat (potong yang sensitif).
- Versi Python, OS, dan cara instalasi (VPS / Termux / Docker).

## Permintaan fitur
Jelaskan kasus penggunaan, bukan solusi. Lebih mudah memilih trade-off bila
kami paham masalah yang ingin dipecahkan.

## Gaya penulisan kode
- Python 3.11+. Format: `ruff` (atur panjang baris 100).
- Penamaan: bahasa Inggris untuk kode, komentar singkat dalam Bahasa Indonesia.
- Public API stabil diberi docstring + type hint.
- Hindari dependensi baru kecuali benar-benar dibutuhkan — diskusi dulu di issue.

## Struktur direktori (ringkas)
- `app/` — kode utama agen (konfigurasi, LLM, alat, dsb).
- `tests/` — uji unit untuk modul `app/`.
- `config/` — contoh konfigurasi (jangan commit `config.toml` asli).
- `contrib/` — skrip instalasi (systemd, dsb).
- `scripts/` — utilitas CLI/demo.

## Lisensi
Dengan berkontribusi, Anda setuju kontribusi Anda dilisensikan di bawah
MIT (lihat `LICENSE`).
