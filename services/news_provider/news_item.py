

from dataclasses import dataclass
from datetime import datetime


@dataclass
class NewsItem:

    title: str
    currency: str
    impact: str
    event_time: datetime
    forecast: str | None
    previous: str | None
    unique_id: str

    def __str__(self) -> str:

        return f"[{self.currency}] {self.title} ({self.impact} impact) at {self.event_time}"