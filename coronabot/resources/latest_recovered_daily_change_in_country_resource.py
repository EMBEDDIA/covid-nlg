import logging
from typing import List, Type

from ..core.models import Fact, Message
from ..core.realize_slots import SlotRealizerComponent
from ..corona_message_generator import CountryData
from .processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: [in {where},] the number of recovered patients increased by {value} [{time}]
en-head: {value} new recoveries in {where} [{time}]
| value_type = Latest:Recovered:DailyChange:Abs
| value > 0

en: [in {where},] the number of recovered patients increased by {value} percentage [{time}]
en-head: {value} % increase in recoveries in {where} [{time}]
| value_type = Latest:Recovered:DailyChange:Percentage
| value > 0

en: [in {where},] the number of recovered patients stayed the same [{time}]
en-head: no new recoveries in {where} [{time}]
| value_type = Latest:Recovered:DailyChange:*
| value = 0
"""


class LatestRecoveredDailyChangeInCountryResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, data: CountryData, context: List[CountryData]) -> List[Message]:
        if len(data.observations) < 3:
            return []

        latest = data.observations[-2]
        comparison_point = data.observations[-3]

        if latest is None or comparison_point is None or latest.recovered is None or comparison_point.recovered is None:
            return []

        delta_day = latest.recovered - comparison_point.recovered

        messages = [
            Message(
                Fact(
                    "[ENTITY:COUNTRY:{}]".format(data.country),
                    "country",
                    "{}:{}".format(comparison_point.timestamp, latest.timestamp),
                    "date_span",
                    delta_day,
                    "Latest:Recovered:DailyChange:Abs",
                    1,
                )
            )
        ]

        if comparison_point.recovered != 0 and delta_day != 0:
            messages.append(
                Message(
                    Fact(
                        "[ENTITY:COUNTRY:{}]".format(data.country),
                        "country",
                        "{}:{}".format(comparison_point.timestamp, latest.timestamp),
                        "date_span",
                        delta_day / comparison_point.recovered * 100,
                        "Latest:Recovered:DailyChange:Percentage",
                        1,
                    )
                )
            )

        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return []
