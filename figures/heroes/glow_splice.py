"""Keep the soft glow of a low resolution render in a high resolution one (for the deep learning panels).

The panels are thousands of small bright points. At about 800 pixels wide several points fall in one pixel, are averaged
in linear light and then pass the view transform, so they merge into a soft wash. At twice that width each point is
resolved and is compressed on its own, the wash fades, and no glare setting brings it back. This takes the fine
detail from the high resolution frame and the low frequencies from a low resolution render of the same frame:
    out = HIGH - blur(HIGH) + blur(LOW upscaled)
SIGMA is the blur width in pixels of the low resolution frame.

Usage: uv run --python 3.11 --with numpy --with scipy --with pillow python glow_splice.py HIGH.png LOW.png OUT.png [SIGMA]
or, with directories for HIGH, LOW and OUT, every f_*.png in HIGH.
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter


def splice(high, low, out, sigma):
    H = Image.open(high).convert('RGB'); L = Image.open(low).convert('RGB')
    s = sigma * H.width / L.width
    A = np.asarray(H, np.float32)
    B = np.asarray(L.resize(H.size, Image.BICUBIC), np.float32)
    im = A + gaussian_filter(B, (s, s, 0)) - gaussian_filter(A, (s, s, 0))
    Image.fromarray(np.clip(im + 0.5, 0, 255).astype(np.uint8)).save(out, compress_level=1)


high, low, out = sys.argv[1:4]
sigma = float(sys.argv[4]) if len(sys.argv) > 4 else 2.5
if os.path.isdir(high):
    os.makedirs(out, exist_ok=True)
    for n in sorted(os.listdir(high)):
        if n.endswith('.png') and os.path.exists(os.path.join(low, n)) and not os.path.exists(os.path.join(out, n)):
            splice(os.path.join(high, n), os.path.join(low, n), os.path.join(out, n), sigma)
else:
    splice(high, low, out, sigma)
