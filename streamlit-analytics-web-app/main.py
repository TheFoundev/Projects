"""Pipeline entry point. Run `python main.py run` or `python main.py demo`."""
import argparse
import json

from src.pipeline import CURRENT_MONTH, cohort_retention, filter_data, load, mrr_by_month, save, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Subscription analytics.")
    parser.add_argument("command", choices=["run", "demo", "info"])
    parser.add_argument("--base-dir", default="artifacts", help="output directory")
    args = parser.parse_args()

    if args.command == "info":
        print("Subscription analytics with Streamlit.")
        print("Run `streamlit run app.py` for the page, or `python main.py run` for the numbers.")
        return

    if args.command == "demo":
        frame = load(base_dir=args.base_dir)
        numbers = summary(frame, CURRENT_MONTH)
        print(f"MRR: {numbers['mrr']:.2f}, ARR: {numbers['arr']:.2f}")
        print(f"Active customers: {numbers['active']}, average fee: {numbers['average_fee']:.2f}")
        print(f"Churn: {numbers['churn_rate'] * 100:.1f}%, net revenue retention: {numbers['net_revenue_retention'] * 100:.1f}%")
        print(mrr_by_month(frame).to_string(index=False))
        print(cohort_retention(frame).to_string(index=False))
        return

    frame = load(base_dir=args.base_dir)
    save(frame, base_dir=args.base_dir)
    print(json.dumps(summary(frame, CURRENT_MONTH), indent=2, default=str))


if __name__ == "__main__":
    main()
