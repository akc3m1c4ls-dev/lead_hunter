from outreach.selector import get_next_lead
from outreach.composer import compose_email, revise_email
from outreach.drafter import review_draft


MAX_REVISIONS = 3


def run_pipeline():
    print("=" * 70)
    print("AUTOMATELABS OUTREACH PIPELINE")
    print("=" * 70)
    print()

    # -----------------------------------------------------
    # 1. SELECT LEAD
    # -----------------------------------------------------

    print("Selecting next lead...")

    lead = get_next_lead()

    if lead is None:
        print("No eligible leads found.")
        return

    print(f"Selected: {lead['business_name']}")
    print(f"Email:    {lead['email']}")
    print(f"Score:    {lead['score']}")
    print()

    # -----------------------------------------------------
    # 2. INITIAL COMPOSITION
    # -----------------------------------------------------

    print("Generating initial draft...")

    draft = compose_email(lead)

    if draft is None:
        print("Composer failed to generate draft.")
        return

    print("Draft generated.")
    print()

    # -----------------------------------------------------
    # 3. REVIEW / REVISION LOOP
    # -----------------------------------------------------

    revision_count = 0
    review = None

    while True:
        print(
            f"Reviewing draft "
            f"(revision {revision_count}/{MAX_REVISIONS})..."
        )

        review = review_draft(lead, draft)

        if review is None:
            print("Drafter failed to review draft.")
            return

        if review["approved"]:
            print("Drafter approved the draft.")
            print()
            break

        print("Drafter requested revision.")

        if review["issues"]:
            print()

            for issue in review["issues"]:
                print(f"  - {issue}")

        print()

        if revision_count >= MAX_REVISIONS:
            print("Maximum revision count reached.")
            print("Draft requires manual review.")
            print()
            break

        revision_count += 1

        print(
            f"Sending revision instructions to Composer "
            f"({revision_count}/{MAX_REVISIONS})..."
        )

        revised_draft = revise_email(
            lead=lead,
            draft=draft,
            feedback=review["revision_instructions"],
        )

        if revised_draft is None:
            print("Composer failed to revise draft.")
            return

        draft = revised_draft

        print("Revision generated.")
        print()

    # -----------------------------------------------------
    # 4. HUMAN REVIEW OUTPUT
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("FINAL OUTREACH DRAFT")
    print("=" * 70)

    print(f"Business: {lead['business_name']}")
    print(f"To:       {lead['email']}")
    print(f"Subject:  {draft['subject']}")
    print()

    print("-" * 70)
    print("EESTI")
    print("-" * 70)
    print()
    print(draft["estonian"])

    print()
    print("-" * 70)
    print("РУССКИЙ")
    print("-" * 70)
    print()
    print(draft["russian"])

    print()
    print("-" * 70)
    print("ENGLISH")
    print("-" * 70)
    print()
    print(draft["english"])

    # -----------------------------------------------------
    # 5. EXPLAIN WHY
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("WHY THIS DRAFT")
    print("=" * 70)

    if review is not None:
        print(review["reasoning"])

    print()
    print(f"Revisions performed: {revision_count}")

    if review and review["approved"]:
        print("Status: APPROVED BY DRAFTER")
    else:
        print("Status: MANUAL REVIEW REQUIRED")

    print("=" * 70)


if __name__ == "__main__":
    run_pipeline()