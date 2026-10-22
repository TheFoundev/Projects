"""Create sharp images, then downsample them for the upscaler."""
import numpy as np
from PIL import Image, ImageDraw


def make_image(seed=0, size=64):
    rng = np.random.default_rng(seed)
    canvas = Image.new("RGB", (size, size), (32, 36, 42))
    draw = ImageDraw.Draw(canvas)
    for _ in range(5):
        x0, y0 = rng.integers(0, size // 2, 2)
        x1, y1 = x0 + rng.integers(8, size // 2), y0 + rng.integers(8, size // 2)
        color = tuple(int(value) for value in rng.integers(70, 240, 3))
        if rng.random() < 0.5:
            draw.rectangle([int(x0), int(y0), int(x1), int(y1)], fill=color)
        else:
            draw.ellipse([int(x0), int(y0), int(x1), int(y1)], fill=color)
    return np.asarray(canvas)


def downsample(image, factor=4):
    height, width = image.shape[:2]
    small = np.asarray(
        Image.fromarray(image).resize((width // factor, height // factor), Image.BICUBIC)
    )
    return small


def load_data(seed=42, quick=False):
    count = 3 if quick else 10
    pairs = []
    for index in range(count):
        high = make_image(seed + index, 48 if quick else 64)
        low = downsample(high, 4)
        pairs.append({"low": low, "high": high})
    return {"pairs": pairs}
