"""Bicubic upscaling with a tunable unsharp mask."""
import numpy as np
from PIL import Image, ImageFilter


def upscale(low, radius=1.2, percent=140, threshold=2):
    height, width = low.shape[:2]
    image = Image.fromarray(low).resize((width * 4, height * 4), Image.BICUBIC)
    image = image.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))
    return np.asarray(image)


def psnr(reference, candidate):
    error = reference.astype(float) - candidate.astype(float)
    mse = float(np.mean(error ** 2))
    if mse == 0:
        return 99.0
    return float(10 * np.log10((255 ** 2) / mse))


def evaluate(pairs, radius=1.2, percent=140):
    scores = []
    errors = []
    for pair in pairs:
        output = upscale(pair["low"], radius, percent)
        height = min(output.shape[0], pair["high"].shape[0])
        width = min(output.shape[1], pair["high"].shape[1])
        output = output[:height, :width]
        target = pair["high"][:height, :width]
        scores.append(psnr(target, output))
        errors.append(float(np.mean(np.abs(target.astype(float) - output.astype(float)))))
    return float(np.mean(scores)), float(np.mean(errors))


def train(data, quick=False):
    best = None
    for percent in (100, 140, 180):
        score, error = evaluate(data["pairs"], percent=percent)
        if best is None or score > best["psnr"]:
            best = {"radius": 1.2, "percent": percent, "psnr": score, "mae": error}
    model = {"radius": best["radius"], "percent": best["percent"]}
    return model, {
        "psnr": round(float(best["psnr"]), 3),
        "mae": round(float(best["mae"]), 3),
        "validation_images": len(data["pairs"]),
    }


def demo(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path

    pair = data["pairs"][0]
    output = upscale(pair["low"])
    print(f"Low resolution: {pair['low'].shape}, output: {output.shape}")
    print(f"PSNR: {psnr(pair['high'], output):.2f} dB")

    Path("artifacts").mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(7, 3.5))
    axes[0].imshow(pair["low"])
    axes[0].set_title("input (4x down)")
    axes[1].imshow(output)
    axes[1].set_title("bicubic + sharpen")
    for axis in axes:
        axis.axis("off")
    fig.tight_layout()
    fig.savefig("artifacts/super_resolution_demo.png", dpi=110)
    plt.close(fig)
