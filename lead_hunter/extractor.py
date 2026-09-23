import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


IMPORTANT_KEYWORDS = {
    "booking": [
        "booking",
        "book",
        "appointment",
        "broneeri",
        "broneerimine",
        "broneering",
        "veebibroneering",
    ],
    "contact": [
        "contact",
        "kontakt",
        "get in touch",
    ],
    "services": [
        "services",
        "service",
        "teenused",
        "teenus",
    ],
    "pricing": [
        "pricing",
        "price",
        "prices",
        "hinnakiri",
        "hind",
    ],
    "about": [
        "about",
        "meist",
        "meie",
    ],
    "faq": [
        "faq",
        "frequently asked",
        "korduma kippuvad",
    ],
    "forms": [
        "form",
        "vorm",
        "application",
        "avaldus",
    ],
    "chatbot": [
        "chatbot",
        "chat bot",
        "virtual assistant",
        "virtual agent",
        "ai assistant",
        "digital assistant",
        "digital agent",
        "virtuaalassistent",
        "virtuaalne assistent",
    ],
}


def extract_title(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    if soup.title:
        return soup.title.get_text(strip=True)

    return None


def extract_description(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    tag = soup.find(
        "meta",
        attrs={"name": "description"},
    )

    if tag:
        return tag.get("content")

    return None


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(["script", "style", "noscript"]):
        element.decompose()

    return soup.get_text(
        separator=" ",
        strip=True,
    )


def extract_links(
    html: str,
    base_url: str,
) -> list[str]:

    soup = BeautifulSoup(html, "html.parser")

    links = []

    for tag in soup.find_all("a", href=True):
        url = urljoin(base_url, tag["href"])
        links.append(url)

    return list(dict.fromkeys(links))


def extract_important_links(
    html: str,
    base_url: str,
) -> list[str]:

    soup = BeautifulSoup(html, "html.parser")

    important_links = []

    for tag in soup.find_all("a", href=True):

        link_text = tag.get_text(
            " ",
            strip=True,
        ).lower()

        href = tag["href"].lower()

        combined = f"{link_text} {href}"

        for keywords in IMPORTANT_KEYWORDS.values():

            if any(
                keyword in combined
                for keyword in keywords
            ):
                url = urljoin(
                    base_url,
                    tag["href"],
                )

                important_links.append(url)
                break

    return list(dict.fromkeys(important_links))


def extract_emails(text: str) -> list[str]:

    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

    return list(
        dict.fromkeys(
            re.findall(pattern, text)
        )
    )


def extract_phones(text: str) -> list[str]:

    pattern = r"""
        (?<!\d)
        (?:\+|00)?\d
        [\d\s().-]{6,}
        \d
        (?!\d)
    """

    matches = re.findall(
        pattern,
        text,
        re.VERBOSE,
    )

    return list(
        dict.fromkeys(
            match.strip()
            for match in matches
        )
    )


def extract_forms(html: str) -> list[str]:

    soup = BeautifulSoup(html, "html.parser")

    forms = []

    for form in soup.find_all("form"):

        action = form.get("action")

        if action:
            forms.append(action)
        else:
            forms.append("inline-form")

    return list(dict.fromkeys(forms))


def extract_documents(
    html: str,
    base_url: str,
) -> list[str]:

    soup = BeautifulSoup(html, "html.parser")

    documents = []

    for tag in soup.find_all("a", href=True):

        href = tag["href"]

        if href.lower().endswith(
            (".pdf", ".doc", ".docx")
        ):
            documents.append(
                urljoin(base_url, href)
            )

    return list(dict.fromkeys(documents))


def extract_signals(
    text: str,
    links: list[str],
) -> list[str]:

    content = (
        text + " " + " ".join(links)
    ).lower()

    signals = []

    signal_keywords = {
        "online_booking": [
            "booking",
            "appointment",
            "broneeri",
            "broneering",
            "veebibroneering",
        ],

        "contact_form": [
            "contact form",
            "kontaktivorm",
        ],

        "whatsapp": [
            "whatsapp",
            "wa.me",
        ],

        "live_chat": [
            "live chat",
            "chat with us",
            "chat now",
            "vestle meiega",
            "vestlus",
        ],

        "chatbot": [
            "chatbot",
            "chat bot",
            "virtual assistant",
            "virtual agent",
            "ai assistant",
            "digital assistant",
            "virtuaalassistent",
            "virtuaalne assistent",
        ],

        "messenger": [
            "messenger",
            "m.me",
        ],

        "telegram": [
            "telegram",
            "t.me",
        ],

        "newsletter": [
            "newsletter",
            "subscribe",
            "tellimus",
            "uudiskiri",
        ],

        "multilingual": [
            "english",
            "estonian",
            "eesti",
            "русский",
            "russian",
            "finnish",
            "suomi",
        ],
    }

    for signal, keywords in signal_keywords.items():

        if any(
            keyword in content
            for keyword in keywords
        ):
            signals.append(signal)

    return signals

def extract_chatbot_signals(html: str) -> list[str]:

    content = html.lower()

    chatbot_patterns = [
        "intercom",
        "tawk.to",
        "tidio",
        "drift",
        "crisp",
        "zendesk",
        "hubspot",
        "livechat",
        "chatra",
        "smartsupp",
    ]

    found = []

    for pattern in chatbot_patterns:
        if pattern in content:
            found.append(pattern)

    return found