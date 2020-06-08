import logging
from typing import List, Type

from ..core.models import Fact, Message
from ..core.realize_slots import SlotRealizerComponent
from ..corona_message_generator import CountryData
from .processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: [in {where},] the number of confirmed cases increased by {value} cases [{time}]
en-head: {value} new cases in {where}
| value_type = Latest:Confirmed:WeeklyChange:Abs
| value > 0

en: [in {where},] the number of confirmed cases increased by {value} percentage [{time}]
en-head: case count increases by {value} % in {where} [{time}]
| value_type = Latest:Confirmed:WeeklyChange:Percentage
| value > 0

en: [in {where},] the number of confirmed cases stayed the same [{time}]
en-head: no new cases [in {where}] [{time}]
| value_type = Latest:Confirmed:WeeklyChange:*
| value = 0
"""


class LatestConfirmedWeeklyChangeInCountryResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, data: CountryData, context: List[CountryData]) -> List[Message]:
        latest = data.observations[-1]
        comparison_point = data.observations[-8]

        if latest is None or comparison_point is None or latest.confirmed is None or comparison_point.confirmed is None:
            return []

        delta_week = latest.confirmed - comparison_point.confirmed

        messages = [
            Message(
                Fact(
                    data.country,
                    "country",
                    "{}:{}".format(str(comparison_point.timestamp), str(latest.timestamp)),
                    "date_span",
                    delta_week,
                    "Latest:Confirmed:WeeklyChange:Abs",
                    1,
                )
            )
        ]

        if comparison_point.confirmed != 0:
            messages.append(
                Message(
                    Fact(
                        data.country,
                        "country",
                        "{}:{}".format(str(comparison_point.timestamp), str(latest.timestamp)),
                        "date_span",
                        delta_week / comparison_point.confirmed * 100,
                        "Latest:Confirmed:WeeklyChange:Percentage",
                        1,
                    )
                )
            )

        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return []
