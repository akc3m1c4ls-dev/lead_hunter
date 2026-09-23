from dataclasses import dataclass, field


@dataclass
class Business:
    name: str
    category: str
    location: str

    website: str | None = None
    phone: str | None = None
    email: str | None = None

    description: str | None = None
    services: list[str] = field(default_factory=list)


@dataclass
class BusinessAnalysis:
    problems: list[str] = field(default_factory=list)
    opportunities: list[str] = field(default_factory=list)
    existing_systems: list[str] = field(default_factory=list)

    target_problem: str = ""
    proposed_solution: str = ""
    evidence: list[str] = field(default_factory=list)
    pitch_angle: str = ""

    reasoning: str = ""
    score_reasoning: str = ""

    confidence: float = 0.0
    score: int = 0
    

@dataclass
class WebsiteResearch:
    url: str

    title: str | None = None
    description: str | None = None

    text: str = ""

    links: list[str] = field(default_factory=list)
    important_links: list[str] = field(default_factory=list)

    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)

    forms: list[str] = field(default_factory=list)
    documents: list[str] = field(default_factory=list)

    signals: list[str] = field(default_factory=list)

    chatbot_platforms: list[str] = field(default_factory=list)