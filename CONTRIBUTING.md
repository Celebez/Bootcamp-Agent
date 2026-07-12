# Berkontribusi ke Bootcamp Agent

Terima kasih atas minat Anda untuk menyempurnakan Bootcamp Agent! Ini adalah
framework pembelajaran yang kecil, jadi perubahan yang sederhana dan mudah dibaca
sangat dihargai.

## Cara mulai
1. Fork repo, lalu clone.
2. Buat virtual environment: `python -m venv .venv && source .venv/bin/activate`
3. Pasang dependensi: `pip install -r requirements.txt`
4. Jalankan `python main.py --setup` untuk mengonfigurasi provider AI Anda.

## Konvensi
- Komentar dan teks yang terlihat pengguna dalam Bahasa Indonesia.
- Jalankan `python tests_offline.py` sebelum mengirim PR.
- Format dengan `ruff` (`pip install ruff && ruff check .`).

## Pull request
- Buat branch fitur dari `master`.
- Jelaskan mengapa perubahan dilakukan, bukan hanya apa yang diubah.
- Pastikan tes offline lulus.
