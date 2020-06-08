import logging
from typing import List, Type

from ..core.models import Fact, Message
from ..core.realize_slots import SlotRealizerComponent
from ..corona_message_generator import CountryData
from .processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: [in {where},] there have been {value} confirmed recoveries [{time}]
en-head: {value} total recovered in {where} [{time}]
| value_type = Latest:Recovered:Total
"""


class LatestRecoveredTotalInCountryResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, data: CountryData, context: List[CountryData]) -> List[Message]:

        latest = data.observations[-2]

        return [
            Message(
                Fact(
                    data.country, "country", latest.timestamp, "date_by", latest.recovered, "Latest:Recovered:Total", 1
                )
            )
        ]

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return []
