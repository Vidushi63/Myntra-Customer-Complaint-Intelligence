
import json
import re
import time
import pandas as pd
from ai_service import ask_ai

INPUT_FILE = "cleaned_reviews.csv"
OUTPUT_FILE = "classified_reviews.csv"

# Test only 10 reviews first to control API usage.
TEST_LIMIT = 600
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

def classify_batch(batch):
    reviews = []

    for idx, row in batch.iterrows():
        reviews.append({
            "index": int(idx),
            "score": int(row["score"]) if pd.notna(row["score"]) else None,
            "review": str(row["content"])[:1500]
        })

    prompt = f"""
Classify each customer review in this JSON input.

For each review, return:
- index: the exact input index
- sentiment: Positive, Neutral, or Negative
- category: one of {CATEGORIES}
- priority: High, Medium, or Low
- is_complaint: true or false
- reason: a short explanation


Guidelines:
- High priority: serious payment/refund problems, severe delivery
  failures, or urgent unresolved issues.
- Medium: a clear but non-urgent problem.
- Low: minor issues or reviews with no urgent problem.
- Positive reviews should normally have is_complaint=false.
- A negative review is not automatically a complaint.
- Classify the actual review text, not just the star rating.
- App/Technical Issue: use ONLY for explicit technical problems,
  such as crashes, bugs, login failures, or payment errors caused
  by the app. General praise like "very nice app" is NOT a technical issue.
- Other: use for general praise, vague reviews, or topics that do
  not fit another category.
- Pricing: use when the review explicitly discusses price, cost,
  discounts, or value for money.
- Delivery: use for delayed, missing, or failed deliveries.
- Refund: use for refund delays or missing refunds.
- Customer Support: use for unresponsive or unhelpful support.
- Product Quality: use for damaged, defective, or poor-quality products.
- Return/Exchange: use for return or exchange problems.
- Payment: use for payment-related issues.
- Assign categories based on the main topic, even for positive reviews.
- Do not invent details that are not stated in the review.
- Use exactly the allowed category and sentiment labels.


Input:
{json.dumps(reviews, ensure_ascii=False)}
"""

    response = ask_ai(
        prompt,
        system_prompt="You are a careful customer-feedback analyst. Follow the requested JSON format exactly."
    )

    try:
        # Extract the JSON array, even if the model adds code fences.
        match = re.search(r"\[.*\]", response, re.DOTALL)
        if not match:
            raise ValueError("No JSON array found in AI response")

        results = json.loads(match.group())

        if not isinstance(results, list):
            raise ValueError("AI response is not a JSON list")

        return results

    except (json.JSONDecodeError, ValueError) as error:
        print("Could not parse this batch:", error)
        print("AI response:", response[:1000])
        return []


def main():
    df = pd.read_csv(INPUT_FILE)

    required_columns = {"content", "score"}
    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Exclude blank reviews from AI requests.
    df = df[df["content"].notna()].copy()
    df = df[df["content"].astype(str).str.strip() != ""]
    df = df.head(TEST_LIMIT).copy()

    if df.empty:
        print("No reviews found to classify.")
        return

    all_results = []
    total = len(df)

    for start in range(0, total, BATCH_SIZE):
        batch = df.iloc[start:start + BATCH_SIZE]

        print(f"Classifying reviews {start + 1}–{start + len(batch)} of {total}...")

        results = classify_batch(batch)
        all_results.extend(results)

        # Brief pause between API requests.
        if start + BATCH_SIZE < total:
            time.sleep(2)

    result_df = pd.DataFrame(all_results)

    if result_df.empty or "index" not in result_df.columns:
        print("No valid classifications returned. Check the errors above.")
        return

    # Keep only results with valid source indexes.
    result_df = result_df.drop_duplicates(subset=["index"])
    result_df = result_df.set_index("index")

    df["source_index"] = df.index
    df = df.join(
        result_df[
            ["sentiment", "category", "priority", "is_complaint", "reason"]
        ],
        on="source_index"
    )

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"\nSaved results to: {OUTPUT_FILE}")
    print(f"Reviews in test: {len(df)}")
    print(f"Successfully classified: {df['sentiment'].notna().sum()}")
    print("\nClassification preview:")

    columns = [
        "content", "score", "sentiment",
        "category", "priority", "is_complaint"
    ]
    print(df[columns].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
