import logging
from typing import List, Type

from ..core.models import Fact, Message
from ..core.realize_slots import SlotRealizerComponent
from ..corona_message_generator import CountryData
from .processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: [in {where},] there have been {value} confirmed cases [{time}]
en-head: {value} total cases in {where} [{time}]
| value_type = Latest:Confirmed:Total
"""


class LatestConfirmedTotalInCountryResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, data: CountryData, context: List[CountryData]) -> List[Message]:

        latest = data.observations[-1]

        return [
            Message(
                Fact(
                    data.country, "country", latest.timestamp, "date_by", latest.confirmed, "Latest:Confirmed:Total", 1
                )
            )
        ]

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return []
