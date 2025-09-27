from typing import List, TypedDict


class ResearchRequest(TypedDict):
    query: str
    max_sources: int


class ResearchNote(TypedDict):
    url: str
    title: str
    summary: str


class ResearchResponse(TypedDict):
    notes: List[ResearchNote]
