import os, sys
from datasets import Dataset
from PIL import Image
from collections import OrderedDict

PARQUET = "/tmp/manoela_train.parquet"
OUT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "input", "plantdisease", "PlantVillage"))

# manoela 'caption' -> canonical Kaggle PlantVillage folder name (the label the notebook stores)
LABEL_MAP = OrderedDict([
    ("Pepper bell Bacterial spot", "Pepper__bell___Bacterial_spot"),
    ("Pepper bell healthy",        "Pepper__bell___healthy"),
    ("Potato Early blight",       "Potato___Early_blight"),
    ("Potato Late blight",        "Potato___Late_blight"),
    ("Potato healthy",            "Potato___healthy"),
    ("Tomato Bacterial spot",     "Tomato_Bacterial_spot"),
    ("Tomato Early blight",       "Tomato_Early_blight"),
    ("Tomato Late blight",        "Tomato_Late_blight"),
    ("Tomato Leaf Mold",          "Tomato_Leaf_Mold"),
    ("Tomato Septoria leaf spot", "Tomato_Septoria_leaf_spot"),
    ("Tomato Spider mites Two spotted spider mite", "Tomato_Spider_mites_Two_spotted_spider_mite"),
    ("Tomato Target Spot",        "Tomato__Target_Spot"),
    ("Tomato YellowLeaf Curl Virus","Tomato__Tomato_YellowLeaf__Curl_Virus"),
    ("Tomato mosaic virus",       "Tomato__Tomato_mosaic_virus"),
    ("Tomato healthy",            "Tomato_healthy"),
])

def main():
    if not os.path.exists(PARQUET):
        sys.exit(f"missing parquet: {PARQUET}")
    os.makedirs(OUT_ROOT, exist_ok=True)
    print(f"[convert] parquet -> {OUT_ROOT}", flush=True)
    ds = Dataset.from_parquet(PARQUET)
    counts = {}
    total = 0
    for row in ds:
        cap = row["caption"]
        folder = LABEL_MAP.get(cap, cap.replace(" ", "_"))
        d = os.path.join(OUT_ROOT, folder)
        os.makedirs(d, exist_ok=True)
        idx = counts.get(folder, 0)
        counts[folder] = idx + 1
        img = row["image"]
        if not isinstance(img, Image.Image):
            img = Image.fromarray(img)
        fn = f"{folder}_{idx:05d}.jpg"
        img.convert("RGB").save(os.path.join(d, fn), "JPEG", quality=85)
        total += 1
        if total % 2000 == 0:
            print(f"[convert] {total} images written", flush=True)
    print(f"[convert] DONE total={total}", flush=True)
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}", flush=True)

if __name__ == "__main__":
    main()
