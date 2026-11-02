"""Status light twinkle for the machine hall loop, composited from two stills of blender_hpc.py.

ON is the hall with its lights, OFF the same frame rendered with NOLED=1. Their difference is the light of the status
LEDs, glow included. Each LED core is labelled, every pixel of that light goes to its nearest core, and each core gets
its own brightness over time, so the racks, floor and ceiling stay exactly as rendered. A fraction of the LEDs
blink, each a whole number of cycles per loop, so the last frame runs into the first. All of this is schematic: the
hall is not a model of a real machine and the blinking carries no data.

Usage:
  uv run --python 3.11 --with numpy --with scipy --with pillow python hall_twinkle.py ON.png OFF.png OUTDIR \
      [--frames 240] [--density 0.35] [--depth 0.9] [--seed 7] [--stats]
--stats prints the frame difference statistics at 800 pixels wide and writes no frames.
"""
import argparse
import os

import numpy as np
from PIL import Image
from scipy import ndimage as nd

ap = argparse.ArgumentParser()
ap.add_argument('on'); ap.add_argument('off'); ap.add_argument('out')
ap.add_argument('--frames', type=int, default=240); ap.add_argument('--density', type=float, default=0.35)
ap.add_argument('--depth', type=float, default=0.9); ap.add_argument('--seed', type=int, default=7)
ap.add_argument('--stats', action='store_true')
args = ap.parse_args()


def load(path, size=None):
    im = Image.open(path).convert('RGB')
    return np.asarray(im.resize(size, Image.BOX) if size else im, np.float32)


size = (800, 450) if args.stats else None
ON, OFF = load(args.on, size), load(args.off, size)
LIGHT = ON - OFF                                         # may dip below zero by a level or two where the denoiser differs
grey = LIGHT.max(2)
cores, n = nd.label(grey > max(24.0, np.percentile(grey, 99.0)))
_, (iy, ix) = nd.distance_transform_edt(cores == 0, return_indices=True)
near = cores[iy, ix] - 1                                 # the core nearest to each pixel

rng = np.random.default_rng(args.seed)
blinks = rng.random(n) < args.density
cycles = rng.integers(2, 7, n)                           # whole cycles per loop keep the loop periodic
phase = rng.random(n)
sharp = rng.uniform(4.0, 12.0, n)                        # short dips, so an LED is lit most of the time


def level(f):
    s = 0.5 + 0.5 * np.cos(2 * np.pi * (cycles * f / args.frames + phase))
    return 1.0 - args.depth * blinks * s ** sharp


def frame(f):
    return np.clip(OFF + LIGHT * level(f)[near][..., None], 0, 255)


print(n, 'LED cores,', int(blinks.sum()), 'blinking')
if args.stats:
    A = np.stack([frame(f) @ np.array([0.299, 0.587, 0.114], np.float32) for f in range(args.frames)]).round()
    d1 = np.abs(np.diff(A, axis=0)).mean((1, 2)); d6 = np.abs(A[6:] - A[:-6]).mean((1, 2))
    print('lag1 median %.3f, lag6 median %.3f, px>12 at lag6 %.4f%%, seam %.3f' % (
        np.median(d1), np.median(d6), 100 * np.median((np.abs(A[6:] - A[:-6]) > 12).mean((1, 2))), np.abs(A[0] - A[-1]).mean()))
else:
    os.makedirs(args.out, exist_ok=True)
    for f in range(args.frames):
        Image.fromarray((frame(f) + 0.5).astype(np.uint8)).save(os.path.join(args.out, 'f_%04d.png' % f), compress_level=1)
