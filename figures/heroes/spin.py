"""Gaia turning about its spin axis: 60 frames of the blueprint render, one full turn, as an animated WebP."""
import math, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
from blueprint import render
import build_heroes as B
OUT = Path(__file__).resolve().parents[2] / "_local/heroes"
m = B.gaia(); V0 = np.array(m.v, float)
frames = []
# the backdrop: the Milky Way from 10.5 million Gaia DR3 red giants (Andrae et al. 2023), dimmed
sk = Image.open(OUT / "sky_giants.png").convert("RGBA"); base = Image.new("RGBA", sk.size, (16, 18, 22, 255)); base.alpha_composite(sk)
SKY = base.crop((700, 300, 1700, 967)).resize((900, 600), Image.LANCZOS)
SKY = Image.blend(Image.new("RGBA", SKY.size, (16, 18, 22, 255)), SKY, 0.62)
for k in range(60):
    a = 2 * math.pi * k / 60; c, s = math.cos(a), math.sin(a)
    m.v = [tuple(v) for v in np.column_stack([V0[:, 0] * c - V0[:, 1] * s, V0[:, 0] * s + V0[:, 1] * c, V0[:, 2]])]
    rgba = render(m, cam=(17.0, -12.5, 5.0), look=(0, 0, 0.6), fov_deg=38, W=900, H=600, materials=B.GREY, ss=2)
    im = Image.fromarray(rgba, "RGBA").crop((30, 30, 870, 590)).resize((900, 600), Image.LANCZOS)
    bg = SKY.copy(); bg.alpha_composite(im)
    frames.append(bg.convert("RGB"))
    print(k, end=" ", flush=True)
frames[0].save(OUT / "gaia_spin.webp", save_all=True, append_images=frames[1:], duration=200, loop=0, quality=86)
frames[0].save(OUT / "gaia_still.png")
