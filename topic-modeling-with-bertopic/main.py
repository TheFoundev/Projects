"""Command line entry point. Run `python main.py train` or `python main.py demo`."""
import argparse
import json
import pickle
from pathlib import Path

from src.data import load_data
from src.model import train, demo


def main() -> None:
    parser = argparse.ArgumentParser(description='Discover topics in a small news corpus.')
    parser.add_argument("command", choices=["train", "demo", "info"])
    parser.add_argument("--quick", action="store_true", help="use a tiny run for smoke tests")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.command == "info":
        print('Discover topics in a small news corpus.')
        print("Run `python main.py train` to fit the model, or `demo` for a sample.")
        return

    data = load_data(seed=args.seed, quick=args.quick)
    if args.command == "demo":
        demo(data)
        return

    model, metrics = train(data, quick=args.quick)
    out = Path("artifacts")
    out.mkdir(exist_ok=True)
    if hasattr(model, "save"):
        try:
            model.save(out / "model.keras")
        except Exception:
            pass
    else:
        try:
            with open(out / "model.pkl", "wb") as handle:
                pickle.dump(model, handle)
        except Exception:
            pass

    print(json.dumps(metrics, indent=2, default=float))
    print("\nSaved model output under artifacts/ (when supported).")


if __name__ == "__main__":
    main()
