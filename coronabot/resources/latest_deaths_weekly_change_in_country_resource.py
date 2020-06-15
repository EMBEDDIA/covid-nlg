import logging
from typing import List, Type

from ..core.models import Fact, Message
from ..core.realize_slots import SlotRealizerComponent
from ..corona_message_generator import CountryData
from .processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: [in {where},] the number of deaths increased by {value} [{time}]
en-head: {value} new deaths in {where} [{time}]
fi: koronakuolemien määrä nousi {value} tapauksella [{where, case=ssa}] [{time}]
fi-head: {value} uutta koronakuolemaa {where, case=ssa} [{time}]
| value_type = Latest:Deaths:WeeklyChange:Abs
| value > 0

en: [in {where},] the number of deaths increased by {value} percentage [{time}]
en-head: deaths count increases by {value} % in {where} [{time}]
fi: koronakuolemien määrä on kasvanut {value} prosentilla [{where, case=ssa}] [{time}]
fi-head: {value} prosentin muutos koronakuolemissa {where, case=ssa} [{time}]
| value_type = Latest:Deaths:WeeklyChange:Percentage
| value > 0

en: [in {where},] the number of deaths stayed the same [{time}]
en-head: no new deaths in {where} [{time}]
fi: koronakuolemien määrässä ei ole tapahtunut muutosta [{where, case=ssa}] [{time}]
fi-head: ei uusia koronakuolemia {where, case=ssa} [{time}]
| value_type = Latest:Deaths:WeeklyChange:*
| value = 0
"""


class LatestDeathsWeeklyChangeInCountryResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, data: CountryData, context: List[CountryData]) -> List[Message]:
        latest = data.observations[-1]
        comparison_point = data.observations[-8]

        if latest is None or comparison_point is None or latest.deaths is None or comparison_point.deaths is None:
            return []

        delta_week = latest.deaths - comparison_point.deaths

        messages = [
            Message(
                Fact(
                    "[ENTITY:COUNTRY:{}]".format(data.country),
                    "country",
                    "{}:{}".format(comparison_point.timestamp, latest.timestamp),
                    "date_span",
                    delta_week,
                    "Latest:Deaths:WeeklyChange:Abs",
                    1,
                )
            )
        ]

        if comparison_point.deaths != 0:
            messages.append(
                Message(
                    Fact(
                        "[ENTITY:COUNTRY:{}]".format(data.country),
                        "country",
                        "{}:{}".format(comparison_point.timestamp, latest.timestamp),
                        "date_span",
                        delta_week / comparison_point.deaths * 100,
                        "Latest:Deaths:WeeklyChange:Percentage",
                        1,
                    )
                )
            )

        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return []
