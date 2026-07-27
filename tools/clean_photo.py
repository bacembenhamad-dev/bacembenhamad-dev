"""Clean up a source photo for ASCII conversion.

Removes the background, evens out lighting with CLAHE, and composites
the subject onto a solid white canvas so the background maps to the
light/empty end of the ASCII glyph ramp instead of the dark end.
"""
import io
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = REPO_ROOT / "assets" / "source-photo.jpg"
DEFAULT_OUTPUT = REPO_ROOT / "assets" / "photo-ready.png"


def apply_clahe(rgb: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)


def clean_photo(source: Path, output: Path) -> None:
    source_bytes = source.read_bytes()
    cutout = remove(source_bytes)  # RGBA PNG bytes, background removed

    subject = Image.open(io.BytesIO(cutout)).convert("RGBA")

    rgb = np.array(subject.convert("RGB"))
    equalized = apply_clahe(rgb)
    equalized_rgba = np.dstack([equalized, np.array(subject)[:, :, 3]])
    subject = Image.fromarray(equalized_rgba, mode="RGBA")

    canvas = Image.new("RGB", subject.size, (255, 255, 255))
    canvas.paste(subject, mask=subject.split()[3])

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
    print(f"wrote {output}")


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT
    clean_photo(src, dst)
