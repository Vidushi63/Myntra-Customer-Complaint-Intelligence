
import json
import re
import time
import pandas as pd
from ai_service import ask_ai

INPUT_FILE = "classified_reviews.csv"
OUTPUT_FILE = "validated_reviews.csv"
BATCH_SIZE = 5

CATEGORIES = [
    "Delivery",
    "Refund",
    "Payment",
    "Product Quality",
    "App/Technical Issue",
    "Customer Support",
    "Return/Exchange",
    "Pricing",
    "Other"
]


def recategorize_batch(batch):
    reviews = []

    for idx, row in batch.iterrows():
        reviews.append({
            "index": int(idx),
            "review": str(row["content"])[:1500],
            "current_category": str(row["category"])
        })

    prompt = f"""
Review the customer feedback and CORRECT its category if needed.

Allowed categories: {CATEGORIES}

Rules:
- Delivery: late, missing, failed, or repeatedly cancelled orders.
- Refund: money not returned or refund delays.
- Payment: failed, duplicate, or incorrect payment charges.
- Product Quality: damaged, defective, or poor-quality products.
- App/Technical Issue: explicit bugs, crashes, login/account
  access errors, loading failures, or technical malfunctions.
- Customer Support: unreachable support, unanswered queries,
  or unhelpful customer service.
- Return/Exchange: problems initiating or completing returns
  or exchanges.
- Pricing: prices, discounts, platform fees, or value for money.
- Other: general praise, vague "bad app" comments, or feedback
  that does not clearly fit another category.

Choose the MAIN issue. If several issues appear, choose the
most important or central issue. Do not infer details that
are not stated. General app praise is NOT a technical issue.
Do not change a category just because the review is negative.

Return ONLY a JSON array with one object per input:
{{"index": input_index, "category": "one allowed category"}}

Input reviews:
{json.dumps(reviews, ensure_ascii=False)}
"""

    response = ask_ai(
        prompt,
        system_prompt="You are a careful customer complaint categorization analyst."
    )

    try:
        match = re.search(r"\[.*\]", response, re.DOTALL)
        if not match:
            raise ValueError("No JSON array found")

        results = json.loads(match.group())

        valid_results = []
        valid_indexes = set(batch.index)

        for item in results:
            idx = item.get("index")
            category = item.get("category")

            if idx in valid_indexes and category in CATEGORIES:
                valid_results.append({
                    "index": idx,
                    "category": category
                })

        return valid_results

    except (json.JSONDecodeError, ValueError, TypeError) as error:
        print("Batch parsing failed:", error)
        print("AI response:", response[:1000])
        return []


def main():
    df = pd.read_csv(INPUT_FILE)

    required = {"content", "category"}
    if not required.issubset(df.columns):
        raise ValueError(f"Input must contain columns: {required}")

    # Work on a copy. Original classified_reviews.csv stays unchanged.
    df = df.copy()
    df["category_original"] = df["category"]

    # Recheck only the category most likely to contain mismatches.
    targets = df.index[
        df["category"].eq("App/Technical Issue")
    ].tolist()

    print(f"Reviews to recategorize: {len(targets)}")

    corrections = []

    for start in range(0, len(targets), BATCH_SIZE):
        indexes = targets[start:start + BATCH_SIZE]
        batch = df.loc[indexes]

        print(
            f"Checking reviews {start + 1}–"
            f"{start + len(batch)} of {len(targets)}..."
        )

        results = recategorize_batch(batch)
        corrections.extend(results)

        if start + BATCH_SIZE < len(targets):
            time.sleep(2)

    # Apply only valid returned category corrections.
    correction_df = pd.DataFrame(corrections)

    if not correction_df.empty:
        correction_df = correction_df.drop_duplicates(
            subset=["index"], keep="last"
        )

        for _, item in correction_df.iterrows():
            df.at[int(item["index"]), "category"] = item["category"]

    df["category_changed"] = (
        df["category_original"] != df["category"]
    )

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"\nSaved: {OUTPUT_FILE}")
    print("Rows:", len(df))
    print("Categories changed:", int(df["category_changed"].sum()))
    print("\nUpdated category counts:")
    print(df["category"].value_counts(dropna=False))
    print("\nCategory changes:")
    print(
        df[df["category_changed"]][
            ["content", "category_original", "category"]
        ].head(20).to_string(index=False)
    )

    print("\nUnchanged original file:", INPUT_FILE)


if __name__ == "__main__":
    main()
