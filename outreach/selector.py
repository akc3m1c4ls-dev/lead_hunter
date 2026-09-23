from outreach.db import get_connection


def get_next_lead():
    """
    Return exactly ONE eligible opportunity.

    Priority:
      1. Highest score
      2. Highest confidence
      3. Oldest ID

    Leads already entered into outreach are skipped.
    Suppressed email addresses are skipped.
    """

    with get_connection() as conn:

        row = conn.execute(
            """
            SELECT
                o.id,
                o.business_name,
                o.category,
                o.location,
                o.website,
                o.phone,
                o.email,

                o.score,
                o.confidence,

                o.problems,
                o.opportunities,
                o.existing_systems,
                o.target_problem,
                o.proposed_solution,
                o.evidence,
                o.pitch_angle,
                o.relevant_pages,
                o.signals,

                o.created_at

            FROM opps AS o

            WHERE o.status = 'done'

              AND o.email IS NOT NULL
              AND TRIM(o.email) != ''

              -- Never contact suppressed addresses
              AND NOT EXISTS (
                  SELECT 1
                  FROM outreach_suppressions AS s
                  WHERE LOWER(TRIM(s.email))
                        = LOWER(TRIM(o.email))
              )

              -- Never pick an opportunity already
              -- registered with Outreach
              AND NOT EXISTS (
                  SELECT 1
                  FROM outreach_contacts AS oc
                  WHERE oc.opp_id = o.id
              )

            ORDER BY
                COALESCE(o.score, 0) DESC,
                COALESCE(o.confidence, 0) DESC,
                o.id ASC

            LIMIT 1
            """
        ).fetchone()

    if row is None:
        return None

    return dict(row)


if __name__ == "__main__":

    lead = get_next_lead()

    if lead is None:
        print("No eligible leads found.")
        raise SystemExit(0)

    print()
    print("=" * 70)
    print("NEXT OUTREACH LEAD")
    print("=" * 70)

    print(f"ID:             {lead['id']}")
    print(f"Business:       {lead['business_name']}")
    print(f"Email:          {lead['email']}")
    print(f"Website:        {lead['website']}")
    print(f"Category:       {lead['category']}")
    print(f"Location:       {lead['location']}")
    print(f"Score:          {lead['score']}")
    print(f"Confidence:     {lead['confidence']}")

    print()
    print("LEAD HUNTER ANALYSIS")
    print("-" * 70)

    print(f"Problems:\n{lead['problems']}\n")
    print(f"Opportunities:\n{lead['opportunities']}\n")
    print(f"Existing systems:\n{lead['existing_systems']}\n")
    print(f"Target problem:\n{lead['target_problem']}\n")
    print(f"Proposed solution:\n{lead['proposed_solution']}\n")
    print(f"Evidence:\n{lead['evidence']}\n")
    print(f"Pitch angle:\n{lead['pitch_angle']}\n")
    print(f"Signals:\n{lead['signals']}\n")
    print(f"Relevant pages:\n{lead['relevant_pages']}\n")