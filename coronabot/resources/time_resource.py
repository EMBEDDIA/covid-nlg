import logging
from enum import Enum
from typing import List, Type

from ..core.models import Message
from ..core.realize_slots import RegexRealizer, SlotRealizerComponent
from ..corona_message_generator import CountryData
from .processor_resource import ProcessorResource

log = logging.getLogger("root")


class TimeResource(ProcessorResource):
    def templates_string(self) -> str:
        return ""

    def parse_messages(self, data: CountryData, context: List[CountryData]) -> List[Message]:
        return []

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return [EnglishDateByRealizer, EnglishDateSpanRealizer]


class EnglishDateByRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[TIME:date_by:([^\]]+)\]", 1, "by [ENTITY:DATE:{}]")


class EnglishDateSpanRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TIME:date_span:([^\]]+):([^\]]+)\]",
            (1, 2),
            "between [ENTITY:DATE:{}] and [ENTITY:DATE:{}]",
        )


class DateFormat(Enum):
    TODAY = 0
    YESTERDAY = 1
    DAY_BEFORE_YESTERDAY = 2
    LAST_WEEK = 7
    YESTERDAY_LAST_WEEK = 8


DATE_EXPRESSIONS = {
    "en": {
        "default": {
            DateFormat.TODAY: "today",
            DateFormat.YESTERDAY: "yesterday",
            DateFormat.DAY_BEFORE_YESTERDAY: "the day before yesterday",
            DateFormat.LAST_WEEK: "the last week",
            DateFormat.YESTERDAY_LAST_WEEK: "the day before yesterday last week",
        }
    }
}
