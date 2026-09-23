import time

from database.db import (
    init_db,
    get_categories,
    get_next_category,
    save_businesses,
    mark_category_done,
    get_pending_businesses,
    update_business_analysis,
)

from lead_hunter.discovery import search_businesses
from lead_hunter.researcher import research_website
from lead_hunter.analyzer import analyze_business


REQUEST_DELAY = 5
MAX_ANALYSES_PER_RUN = 50


def get_discovery_limit(score: int) -> int:

    if score >= 90:
        return 30

    if score >= 80:
        return 25

    if score >= 70:
        return 20

    if score >= 60:
        return 15

    if score >= 40:
        return 10

    return 5


def discover_next_category(location: str):

    category_data = get_next_category(location)

    if category_data is None:
        print("No pending categories.")
        return False

    category = category_data["category"]
    score = category_data["score"]

    limit = get_discovery_limit(score)

    print("=" * 60)
    print(f"CATEGORY: {category}")
    print(f"SCORE: {score}")
    print(f"DISCOVERY LIMIT: {limit}")

    businesses = search_businesses(
        category,
        location,
        limit,
    )

    if not businesses:
        print(f"✗ Discovery failed for {category}")
        print("  Category remains pending.")
        return False

    print(f"FOUND: {len(businesses)}")

    save_businesses(businesses)

    mark_category_done(
        location,
        category,
    )

    print(f"✓ {category} → DONE")

    return True


def analyze_pending():

    businesses = get_pending_businesses(
        limit=MAX_ANALYSES_PER_RUN
    )

    if not businesses:
        print("No pending businesses.")
        return

    print("=" * 60)
    print(f"PENDING BUSINESSES: {len(businesses)}")

    for business in businesses:

        print("=" * 60)
        print(f"BUSINESS: {business.name}")
        print(f"CATEGORY: {business.category}")

        research = research_website(business)

        if not research:
            print("  ✗ Research failed/skipped")
            continue

        time.sleep(REQUEST_DELAY)

        analysis = analyze_business(
            business,
            research,
        )

        update_business_analysis(
            business,
            research,
            analysis,
        )

        print(f"  SCORE: {analysis.score}")
        print(f"  ✓ {business.name} → DONE")


def main():

    location = "Tallinn"

    init_db()

    categories = get_categories(location)

    if not categories:
        raise RuntimeError(
            f"No categories found for {location}. "
            "Run selector.py first."
        )

    while True:

        category_data = get_next_category(location)

        if category_data is None:
            print("No more pending categories.")
            break

        discover_next_category(location)

        analyze_pending()

if __name__ == "__main__":
    main()