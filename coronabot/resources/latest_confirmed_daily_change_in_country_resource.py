import logging
from typing import List, Type

from ..core.models import Fact, Message
from ..core.realize_slots import SlotRealizerComponent
from ..corona_message_generator import CountryData
from .processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: [in {where},] the number of confirmed cases increased by {value} cases [{time}]
en-head: {value} new COVID-19 cases in {where}
fi: vahvistettujen tapausten määrä nousi {value} tapauksella [{where, case=ssa}] [{time}]
fi-head: {value} uutta koronatapausta {where, case=ssa} [{time}]
| value_type = Latest:Confirmed:DailyChange:Abs
| value > 0

en: [in {where},] the number of confirmed cases increased by {value} percentage [{time}]
en-head: COVID-19 case count increases by {value} % in {where} [{time}]
fi: vahvistettujen tapausten määrä nousi {value} prosenttia [{where, case=ssa}] [{time}]
fi-head: {value} prosentin nousu vahvistetuissa koronatapauksissa {where, case=ssa} [{time}]
| value_type = Latest:Confirmed:DailyChange:Percentage
| value > 0

en: [in {where},] the number of confirmed cases stayed the same [{time}]
en-head: no new COVID-19 cases [in {where}] [{time}]
fi: vahvistettujen tapausten määrässä ei tapahtunut muutosta [{where, case=ssa}] [{time}]
fi-head: ei uusia koronatapauksia {where, case=ssa} [{time}]
| value_type = Latest:Confirmed:DailyChange:*
| value = 0
"""


class LatestConfirmedDailyChangeInCountryResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, data: CountryData, context: List[CountryData]) -> List[Message]:
        latest = data.observations[-1]
        comparison_point = data.observations[-2]

        if latest is None or comparison_point is None or latest.confirmed is None or comparison_point.confirmed is None:
            return []

        delta_day = latest.confirmed - comparison_point.confirmed

        messages = [
            Message(
                Fact(
                    "[ENTITY:COUNTRY:{}]".format(data.country),
                    "country",
                    "{}:{}".format(str(comparison_point.timestamp), str(latest.timestamp)),
                    "date_span",
                    delta_day,
                    "Latest:Confirmed:DailyChange:Abs",
                    1,
                )
            )
        ]

        if comparison_point.confirmed != 0:
            messages.append(
                Message(
                    Fact(
                        "[ENTITY:COUNTRY:{}]".format(data.country),
                        "country",
                        "{}:{}".format(str(comparison_point.timestamp), str(latest.timestamp)),
                        "date_span",
                        delta_day / comparison_point.confirmed * 100,
                        "Latest:Confirmed:DailyChange:Percentage",
                        1,
                    )
                )
            )

        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return []
