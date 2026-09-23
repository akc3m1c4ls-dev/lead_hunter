import requests
import certifi

from lead_hunter.extractor import (
    extract_chatbot_signals,
    extract_description,
    extract_documents,
    extract_emails,
    extract_forms,
    extract_important_links,
    extract_links,
    extract_signals,
    extract_text,
    extract_title,
    extract_phones,
)

from lead_hunter.models import Business, WebsiteResearch


def research_website(
    business: Business,
) -> WebsiteResearch | None:

    if not business.website:
        return None

    try:
        response = requests.get(
            business.website,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "Chrome/140.0 Safari/537.36"
                )
            },
            timeout=10,
            verify=certifi.where(),
        )

        response.raise_for_status()

    except requests.RequestException as e:
        print(
            f"    Research failed: "
            f"{business.name} | {e}"
        )
        return None

    html = response.text

    text = extract_text(html)

    links = extract_links(
        html,
        business.website,
    )

    return WebsiteResearch(
        url=business.website,

        title=extract_title(html),

        description=extract_description(html),

        text=text,

        links=links,

        important_links=extract_important_links(
            html,
            business.website,
        ),

        emails=extract_emails(text),

        phones=extract_phones(text),

        forms=extract_forms(html),

        documents=extract_documents(
            html,
            business.website,
        ),

        signals=extract_signals(
            text,
            links,
        ),

        chatbot_platforms=extract_chatbot_signals(
            html,
        ),
    )