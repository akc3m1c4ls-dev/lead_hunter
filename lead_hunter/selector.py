
# =========================================
#
# THE UTILITY IS RANKING categories ONLY
#
# =========================================
#
# RUN ONCE TO GENERATE category TABLE 
#
# =========================================
# You can edit CATEGORIES list or 'location' 
# variable to achive result you want 
# ========================================
# from project root:
# python3 -m lead_hunter.selector


import json

from google import genai

from config import GEMINI, MODEL 
from database.db import init_db, save_categories


client = genai.Client(api_key=GEMINI)

init_db()

CATEGORIES = [
    # Healthcare
    "dentist",
    "medical clinic",
    "private doctor",
    "physiotherapy clinic",
    "psychologist",
    "psychotherapist",
    "chiropractor",
    "massage therapist",
    "beauty clinic",
    "veterinary clinic",
    "optician",
    "pharmacy",

    # Beauty & Personal Care
    "beauty salon",
    "hair salon",
    "barbershop",
    "nail salon",
    "lash salon",
    "tattoo studio",
    "spa",
    "wellness center",

    # Home & Local Services
    "electrician",
    "plumber",
    "heating contractor",
    "air conditioning contractor",
    "roofer",
    "general contractor",
    "renovation contractor",
    "painting contractor",
    "flooring contractor",
    "window installation",
    "door installation",
    "cleaning service",
    "home cleaning service",
    "pest control",
    "landscaping service",
    "garden service",
    "moving company",
    "locksmith",
    "appliance repair",
    "handyman",

    # Automotive
    "car repair",
    "auto electrician",
    "car detailing",
    "car wash",
    "tire shop",
    "auto body shop",
    "car dealership",
    "motorcycle repair",

    # Professional Services
    "real estate agency",
    "property management",
    "law firm",
    "accounting firm",
    "tax consultant",
    "insurance agency",
    "financial advisor",
    "architect",
    "engineering consultant",
    "marketing agency",
    "advertising agency",
    "web design agency",
    "IT services",
    "business consultant",
    "recruitment agency",
    "translation agency",
    "photographer",

    # Hospitality
    "hotel",
    "guest house",
    "hostel",
    "bed and breakfast",
    "restaurant",
    "small restaurant",
    "cafe",
    "coffee shop",
    "bakery",
    "pizzeria",
    "fast food restaurant",
    "catering service",
    "event venue",
    "wedding venue",

    # Retail
    "florist",
    "flower shop",
    "gift shop",
    "jewelry store",
    "clothing store",
    "shoe store",
    "furniture store",
    "home decor store",
    "electronics store",
    "pet store",
    "bike shop",
    "sports store",
    "specialty food store",
    "wine shop",

    # Fitness & Recreation
    "gym",
    "fitness center",
    "personal trainer",
    "yoga studio",
    "pilates studio",
    "dance studio",
    "martial arts school",
    "swimming school",
    "sports club",

    # Education
    "language school",
    "driving school",
    "music school",
    "tutoring center",
    "training center",
    "private school",
    "kindergarten",

    # Events & Creative
    "wedding planner",
    "event planner",
    "party planner",
    "DJ service",
    "entertainment agency",
    "florist",
    "photography studio",
    "video production",

    # Travel & Tourism
    "travel agency",
    "tour operator",
    "tour guide",
    "car rental",
    "bike rental",
    "boat rental",

    # Other Local Businesses
    "funeral home",
    "dry cleaner",
    "laundromat",
    "tailor",
    "shoe repair",
    "print shop",
    "sign shop",
    "storage facility",
]


def select_categories(location: str) -> list[dict]:

    categories = "\n".join(
        f"- {category}"
        for category in CATEGORIES
    )

    prompt = f"""
You are ranking business categories for an automation
lead-generation agent.

LOCATION:
{location}

CATEGORIES:
{categories}

Your task is to rank ALL categories by how promising
they are for finding businesses that are likely to have
valuable, realistic, and sellable software automation
opportunities.

The goal is NOT to determine which industries can
theoretically use automation.

The goal is to determine which categories are most likely
to contain businesses with problems that an automation
developer could realistically solve and sell.

Consider:

- repetitive administrative work
- customer inquiry volume
- lead qualification
- appointment and booking workflows
- follow-ups and reminders
- document and data processing
- communication across multiple channels
- integrations between business systems
- manual workflows that small businesses commonly have
- potential business value of solving these problems
- likelihood that small and medium-sized businesses in
  the category would realistically pay for automation

IMPORTANT:

Do not assume that every business in a category has these
problems.

Score based on the EXPECTED LIKELIHOOD of finding
sellable automation opportunities within the category.

A category should score higher when:
- businesses commonly have repetitive workflows
- those workflows are valuable to automate
- the problems are likely to still exist in real businesses
- automation can produce a clear business benefit
- the solution can realistically be sold to a small or
  medium-sized business

A category should score lower when:
- automation opportunities are usually minor
- businesses commonly already use mature software that
  solves the main workflows
- automation would require highly specialized systems
  or infrastructure
- opportunities are difficult to sell to typical SMBs
- the potential benefit is mostly theoretical

Do NOT rank based on:
- company size
- popularity
- revenue
- industry prestige
- how technologically interesting the industry is

Do not assume that a category with many appointments,
customers, or employees automatically deserves a high score.

CATEGORY SCORE:

Score each category from 0 to 100.

90-100: Exceptional lead-hunting potential
80-89:  Very high lead-hunting potential
70-79:  High lead-hunting potential
60-69:  Moderate lead-hunting potential
40-59:  Low lead-hunting potential
0-39:   Very low lead-hunting potential

The score represents CATEGORY PRIORITY for this
lead-generation agent, not the score of an individual
business.

For every category, provide a SHORT DESCRIPTION of no more
than ONE SENTENCE explaining the main reason for its score.

Return ALL categories.

Order them from highest score to lowest score.

Return ONLY valid JSON:

{{
    "categories": [
        {{
            "name": "category",
            "score": 95,
            "reason": "Short one-sentence explanation."
        }}
    ]
}}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": {
                "type": "OBJECT",
                "properties": {
                    "categories": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "name": {
                                    "type": "STRING",
                                },
                                "score": {
                                    "type": "INTEGER",
                                },
                                "reason": {
                                    "type": "STRING",
                                },
                            },
                            "required": [
                                "name",
                                "score",
                                "reason",
                            ],
                        },
                    },
                },
                "required": ["categories"],
            },
        },
    )

    data = json.loads(response.text)

    return data["categories"]


def main():
    location = "Tallinn"

    results = select_categories(location)

    save_categories(
        location,
        results,
    )


if __name__ == "__main__":
    main()