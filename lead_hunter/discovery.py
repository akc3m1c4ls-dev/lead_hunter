import requests
from config import PLACES_API
import time

from lead_hunter.models import Business



GOOGLE_PLACES_URL = "https://places.googleapis.com/v1/places:searchText"


def search_businesses(
    category: str,
    location: str,
    limit: int,
) -> list[Business]:

    api_key = PLACES_API

    if not api_key:
        raise RuntimeError(
            "GOOGLE_MAPS_API_KEY is not set in .env"
        )

    query = f"{category} in {location}"

    for attempt in range(2):

        try:
            response = requests.post(
                GOOGLE_PLACES_URL,
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": api_key,
                    "X-Goog-FieldMask": (
                        "places.displayName,"
                        "places.formattedAddress,"
                        "places.websiteUri,"
                        "places.nationalPhoneNumber"
                    ),
                },
                json={
                    "textQuery": query,
                    "pageSize": limit,
                },
                timeout=20,
            )

            response.raise_for_status()
            data = response.json()
            break

        except requests.RequestException as e:

            print(
                f"    Discovery attempt {attempt + 1}/2 failed: {e}"
            )

            if attempt == 1:
                return []

            time.sleep(3)

    businesses = []

    for place in data.get("places", []):

        businesses.append(
            Business(
                name=place["displayName"]["text"],
                category=category,
                location=place.get(
                    "formattedAddress",
                    location,
                ),
                website=place.get("websiteUri"),
                phone=place.get("nationalPhoneNumber"),
            )
        )

    return businesses
