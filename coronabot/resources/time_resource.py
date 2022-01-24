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
        return [
            EnglishDateByRealizer,
            EnglishDateRealizer,
            EnglishDateSpanRealizer,
            EnglishDuringYesterdayRealizer,
            # EnglishDuringLastWeekRealizer,
            FinnishDateSpanRealizer,
            FinnishDateRealizer,
            FinnishDateByRealizer,
        ]


class EnglishDateByRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[TIME:date_by:([^\]]+)\]", 1, "by [ENTITY:DATE:{}]")


class EnglishDateRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[TIME:date:([^\]]+)\]", 1, "[ENTITY:DATE:{}]")


class FinnishDateByRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[TIME:date_by:([^\]]+)\]",
            1,
            "[ENTITY:DATE:{}] mennessä",
            add_attributes={0: {"date-expr-type": "eiliseen"}},
        )


class FinnishDateRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[TIME:date:([^\]]+)\]",
            1,
            "[ENTITY:DATE:{}]",
            add_attributes={0: {"date-expr-type": "eilen"}},
        )


class EnglishDateSpanRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TIME:date_span:([^\]]+):([^\]]+)\]",
            (1, 2),
            "between [ENTITY:DATE:{}] and [ENTITY:DATE:{}]",
        )


class EnglishDuringYesterdayRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "en", r"between the day before yesterday and yesterday", [], "during yesterday",
        )


class EnglishDuringLastWeekRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "en", r"between the day before yesterday last week and yesterday", [], "in the last week",
        )


class FinnishDateSpanRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[TIME:date_span:([^\]]+):([^\]]+)\]",
            (1, 2),
            "[ENTITY:DATE:{}] ja [ENTITY:DATE:{}] välillä",
            add_attributes={0: {"date-expr-type": "eilisen"}, 2: {"date-expr-type": "eilisen"}},
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
        },
    },
    "fi": {
        "eilen": {
            DateFormat.TODAY: "tänään",
            DateFormat.YESTERDAY: "eilen",
            DateFormat.DAY_BEFORE_YESTERDAY: "toissapäivänä",
            DateFormat.LAST_WEEK: "viime viikkolla",
            DateFormat.YESTERDAY_LAST_WEEK: "viime viikkolla",
        },
        "eilisen": {
            DateFormat.TODAY: "tämän päivän",
            DateFormat.YESTERDAY: "eilisen",
            DateFormat.DAY_BEFORE_YESTERDAY: "toissapäivän",
            DateFormat.LAST_WEEK: "viime viikon",
            DateFormat.YESTERDAY_LAST_WEEK: "viime viikon",
        },
        "eiliseen": {
            DateFormat.TODAY: "tähän päivään",
            DateFormat.YESTERDAY: "eiliseen",
            DateFormat.DAY_BEFORE_YESTERDAY: "toissapäivään",
            DateFormat.LAST_WEEK: "viime viikkoon",
            DateFormat.YESTERDAY_LAST_WEEK: "viime viikkoon",
        },
    },
}
