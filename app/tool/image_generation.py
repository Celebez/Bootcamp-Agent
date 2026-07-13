"""Alat generasi gambar via NVIDIA GenAI (default: FLUX.1-dev).

Memanggil endpoint OpenAI-compatible images/generations di
https://ai.api.nvidia.com/v1/genai/<model> dengan HTTP murni (tanpa
dependensi eksternal). Kredensial & model diambil dari [image] di
config.toml atau env OML_IMAGE_*, dengan fallback default NVIDIA FLUX
agar alat tetap siap meski user belum mengisi API key sendiri.
"""
from __future__ import annotations

import asyncio
import base64
import binascii
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from app.config import config
from app.tool.base import BaseTool, ToolResult

_OUTPUT_RE = re.compile(r"[/\\]")
_SAFE_RE = re.compile(r"[^a-zA-Z0-9._-]")


def _slugify(text: str, limit: int = 40) -> str:
    s = _SAFE_RE.sub("_", (text or "image").strip().lower())
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:limit] or "image"


class ImageGeneration(BaseTool):
    name: str = "image_generation"
    description: str = (
        "Hasilkan gambar dari prompt teks menggunakan model image-generation "
        "(default NVIDIA FLUX.1-dev via NVIDIA GenAI). Mengembalikan path "
        "berkas PNG yang disimpan di workspace serta pratinjau base64. "
        "Gunakan saat user meminta membuat/gambar/membuat ilustrasi."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Deskripsi gambar yang diinginkan (bisa Bahasa Indonesia).",
            },
            "model": {
                "type": "string",
                "description": "ID model opsional (default: black-forest-labs/flux.1-dev).",
                "default": None,
            },
            "aspect_ratio": {
                "type": "string",
                "description": "Rasio opsional: 'landscape' (16:9), 'portrait' (9:16), 'square' (1:1).",
                "default": "landscape",
            },
            "filename": {
                "type": "string",
                "description": "Nama berkas opsional (tanpa ekstensi).",
                "default": None,
            },
        },
        "required": ["prompt"],
    }

    @staticmethod
    def _settings():
        img = config.image
        if img is None:
            # import di sini untuk menghindari siklus-impor saat startup
            from app.config import ImageSettings

            img = ImageSettings()
        return img

    @staticmethod
    def _decode(data: str) -> bytes:
        # Coba base64 standar, lalu URL-safe.
        try:
            return base64.b64decode(data, validate=True)
        except (binascii.Error, ValueError):
            pass
        try:
            return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
        except Exception:
            return base64.b64decode(data)

    async def execute(
        self,
        prompt: str,
        model: str = None,
        aspect_ratio: str = "landscape",
        filename: str = None,
    ) -> ToolResult:
        img = self._settings()
        # default model & endpoint dari config image
        model_id = model or img.model or "black-forest-labs/flux.1-dev"
        base_url = (img.base_url or "https://ai.api.nvidia.com/v1/genai/").rstrip("/")
        url = f"{base_url}/{model_id}"
        api_key = img.api_key or ""

        if not api_key:
            return self.fail_response(
                "API key image-generation kosong. Isi [image].api_key di config.toml "
                "atau env OML_IMAGE_API_KEY (default NVIDIA FLUX.1-dev)."
            )

        ar = aspect_ratio or "landscape"
        # NVIDIA GenAI FLUX.1-dev: body hanya butuh "prompt" + "mode".
        # mode valid: "base" (default text-to-image), "canny", "depth".
        payload = {
            "prompt": prompt,
            "mode": "base",
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=300) as resp:
                raw = resp.read()
                status = resp.status
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", "replace")[:400]
            except Exception:
                pass
            return self.fail_response(f"HTTP {e.code}: {e.reason} {detail}".strip())
        except urllib.error.URLError as e:
            return self.fail_response(f"Jaringan gagal: {e.reason}")
        except Exception as e:
            return self.fail_response(f"Permintaan gagal: {type(e).__name__}: {e}")

        if status != 200:
            return self.fail_response(f"HTTP {status}: {raw.decode('utf-8', 'replace')[:400]}")

        # Parsing respons. Dua format dikenali:
        #  - OpenAI-compatible: choices[].image_base64 / b64_json / image_url
        #  - NVIDIA GenAI: artifacts[].base64
        try:
            data = json.loads(raw)
        except Exception as e:
            return self.fail_response(f"Respons bukan JSON: {e}")

        b64 = None
        try:
            # Format NVIDIA GenAI
            if isinstance(data, dict) and data.get("artifacts"):
                arts = data["artifacts"]
                if arts and isinstance(arts[0], dict):
                    b64 = arts[0].get("base64")
            # Format OpenAI-compatible
            if not b64 and isinstance(data, dict):
                choice = data.get("choices", [{}])[0] if data.get("choices") else {}
                if isinstance(choice, dict):
                    if choice.get("image_base64"):
                        b64 = choice["image_base64"]
                    elif choice.get("image_url", "").startswith("data:"):
                        b64 = choice["image_url"].split(",", 1)[1]
                    elif choice.get("b64_json"):
                        b64 = choice["b64_json"]
                    elif choice.get("image_url"):
                        return self.fail_response(
                            f"Model mengembalikan URL (bukan base64): {choice['image_url']}"
                        )
            if not b64 and isinstance(data, dict):
                for k in ("image_base64", "b64_json"):
                    if data.get(k):
                        b64 = data[k]
                        break
        except Exception:
            pass

        if not b64:
            return self.fail_response(
                f"Tidak ada field gambar dalam respons: {json.dumps(data)[:300]}"
            )

        try:
            img_bytes = self._decode(b64)
        except Exception as e:
            return self.fail_response(f"Gagal decode gambar: {e}")

        # Simpan ke workspace/images
        out_dir = Path(config.root_path) / img.output_dir
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return self.fail_response(f"Gagal membuat direktori output: {e}")

        fname = f"{_slugify(filename) or _slugify(prompt)}.png"
        out_path = out_dir / fname
        # hindari tumpang tindih
        n = 1
        while out_path.exists():
            out_path = out_dir / f"{Path(fname).stem}_{n}.png"
            n += 1
        try:
            out_path.write_bytes(img_bytes)
        except Exception as e:
            return self.fail_response(f"Gagal menulis berkas: {e}")

        rel = os.path.relpath(out_path, config.root_path)
        return ToolResult(
            output=(
                f"Gambar dihasilkan dengan model '{model_id}'.\n"
                f"Disimpan di: {rel}\n"
                f"Path absolut: {out_path}\n"
                f"Ukuran: {len(img_bytes)} byte"
            ),
            base64_image=base64.b64encode(img_bytes).decode("utf-8"),
        )
