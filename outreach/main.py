import time

from selector import get_next_lead
from composer import compose_email, revise_email
from drafter import review_draft
from designer import render_draft_with_ai
from sender import send_email, TEST_MODE, TEST_EMAIL, TEST_LIMIT, LIVE_LIMIT
from db import init_outreach_db, get_or_create_campaign, record_successful_send


MAX_REVISIONS = 3
SEND_DELAY_SECONDS = 2
PIPELINE_RETRY_SECONDS = 10
SEND_RETRY_SECONDS = 15


def draft_to_text(draft: dict) -> str:
    """Turn Composer output into the raw text consumed by Designer."""
    return f"""SUBJECT:\n{draft['subject']}\n\nESTONIAN:\n{draft['estonian']}\n\nRUSSIAN:\n{draft['russian']}\n\nENGLISH:\n{draft['english']}"""


def prepare_approved_draft(lead: dict) -> dict | None:
    """Compose, review and revise one lead until approved."""
    draft = compose_email(lead)
    if draft is None:
        print("Composer failed.")
        return None

    for revision_count in range(MAX_REVISIONS + 1):
        print(f"Reviewing draft ({revision_count}/{MAX_REVISIONS})...")
        review = review_draft(lead, draft)

        if review is None:
            print("Drafter failed.")
            return None

        if review.get("approved"):
            print("Drafter approved the draft.")
            return draft

        print("Drafter rejected the draft.")
        for issue in review.get("issues") or []:
            print(f"  - {issue}")

        if revision_count >= MAX_REVISIONS:
            print("Maximum revisions reached. Skipping this lead.")
            return None

        feedback = review.get("revision_instructions") or "Fix the review issues."
        draft = revise_email(lead=lead, draft=draft, feedback=feedback)
        if draft is None:
            print("Composer revision failed.")
            return None

    return None


def is_brevo_authorization_error(exc: Exception) -> bool:
    """Return True for Brevo auth / authorised-IP failures."""
    message = str(exc).lower()
    status_code = getattr(exc, "status_code", None)
    return (
        status_code in (401, 403)
        or "status_code: 401" in message
        or "status_code: 403" in message
        or "unrecognised ip address" in message
        or "unauthorized" in message
        or "authorised_ips" in message
    )


def send_until_success(*, html: str, draft: dict, lead: dict):
    """
    Keep the current business locked while sending.

    Temporary send failures retry the SAME already-rendered email. Brevo
    authentication / authorised-IP failures abort the run immediately so we do
    not waste Gemini quota generating emails that cannot be sent.
    """
    attempt = 0

    while True:
        attempt += 1
        try:
            print(f"Sending through Brevo (attempt {attempt})...")
            return send_email(
                html=html,
                subject=draft["subject"],
                recipient_email=lead["email"],
                recipient_name=lead["business_name"],
            )
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            if is_brevo_authorization_error(exc):
                raise RuntimeError(
                    "BREVO AUTHORIZATION FAILED. The pipeline has been stopped. "
                    "Authorize the current IP in Brevo, then rerun. The current "
                    "business was NOT skipped and no new business was processed.\n"
                    f"Brevo error: {exc}"
                ) from exc

            print(f"Brevo send failed for {lead['business_name']}: {exc}")
            print(
                f"Keeping the SAME business. Retrying the SAME rendered email "
                f"in {SEND_RETRY_SECONDS}s..."
            )
            time.sleep(SEND_RETRY_SECONDS)


def run_pipeline():
    print("=" * 70)
    print("AUTOMATELABS OUTREACH PIPELINE")
    print("=" * 70)
    print(f"TEST_MODE : {TEST_MODE}")
    if TEST_MODE:
        print(f"All mail  : {TEST_EMAIL}")
        print(f"Target    : {TEST_LIMIT} successful test emails")
    else:
        print(f"LIVE MODE : real business recipients")
        print(f"LIVE LIMIT: {LIVE_LIMIT} successful emails")
    print("=" * 70)

    init_outreach_db()
    run_limit = TEST_LIMIT if TEST_MODE else LIVE_LIMIT
    campaign_id = None if TEST_MODE else get_or_create_campaign()

    sent = 0
    completed_ids = set()
    pipeline_attempt = 0
    stopped_reason = None

    while sent < run_limit:
        # Only successfully SENT businesses are excluded. A business stays
        # locked as the current one until its email has actually been sent.
        lead = get_next_lead(exclude_ids=completed_ids)

        if lead is None:
            print("No more eligible leads found.")
            break

        pipeline_attempt += 1

        print()
        print("#" * 70)
        print(f"CURRENT BUSINESS | SENT {sent}/{run_limit}")
        print("#" * 70)
        print(f"Business : {lead['business_name']}")
        print(f"Real To  : {lead['email']}")
        print(f"Score    : {lead['score']}")
        print(f"Pipeline attempt for current business: {pipeline_attempt}")

        try:
            draft = prepare_approved_draft(lead)
            if draft is None:
                print(
                    f"Pipeline did not finish for {lead['business_name']}. "
                    f"Keeping the SAME business and retrying in "
                    f"{PIPELINE_RETRY_SECONDS}s..."
                )
                time.sleep(PIPELINE_RETRY_SECONDS)
                continue

            print("Designing final HTML...")
            html, _designed = render_draft_with_ai(
                company_name=lead["business_name"],
                raw_draft=draft_to_text(draft),
                preferred_language="et",
                unsubscribe_url="#unsubscribe",
            )

            # Once HTML exists, do NOT run another business or regenerate this
            # email merely because Brevo has a temporary send problem.
            message_id = send_until_success(html=html, draft=draft, lead=lead)

            # A business becomes completed only after Brevo accepted the email.
            # In LIVE_MODE, persist the accepted send before moving to another lead.
            if not TEST_MODE:
                contact_id, db_message_id = record_successful_send(
                    opp_id=lead["id"],
                    campaign_id=campaign_id,
                    subject=draft["subject"],
                    html=html,
                    provider_message_id=message_id,
                )
                print(f"DB persisted | contact={contact_id} message={db_message_id}")

            completed_ids.add(lead["id"])
            sent += 1
            pipeline_attempt = 0
            print(f"SUCCESS {sent}/{run_limit} | Brevo ID: {message_id}")

            if sent < run_limit:
                time.sleep(SEND_DELAY_SECONDS)

        except KeyboardInterrupt:
            print("\nStopped by user. Current business was not skipped.")
            stopped_reason = "Stopped by user"
            break
        except RuntimeError as exc:
            # Infrastructure/auth failures stop the whole conveyor belt. This
            # is intentional: never burn Gemini quota on the next businesses.
            if "BREVO AUTHORIZATION FAILED" in str(exc):
                print()
                print("!" * 70)
                print(str(exc))
                print("!" * 70)
                stopped_reason = "Brevo authorization failure"
                break
            raise
        except Exception as exc:
            print(f"PIPELINE FAILED for {lead['business_name']}: {exc}")
            print(
                f"NOT skipping it. Keeping the SAME business and retrying the "
                f"pipeline in {PIPELINE_RETRY_SECONDS}s..."
            )
            time.sleep(PIPELINE_RETRY_SECONDS)

    print()
    print("=" * 70)
    print("RUN COMPLETE")
    mode_label = "test" if TEST_MODE else "live"
    print(f"Successful {mode_label} emails: {sent}/{run_limit}")
    print(f"Businesses completed: {len(completed_ids)}")
    if stopped_reason:
        print(f"Stopped reason: {stopped_reason}")
    if TEST_MODE:
        print("Real outreach DB contacts were NOT created in TEST_MODE.")
    else:
        print("Successful live sends were persisted to the outreach DB.")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline()
