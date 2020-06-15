import logging
from typing import List, Type

from ..core.models import Fact, Message
from ..core.realize_slots import SlotRealizerComponent
from ..corona_message_generator import CountryData
from .processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: [in {where},] there have been {value} confirmed deaths [{time}]
en-head: {value} total dead in {where} [{time}]
fi: {where, case=ssa} on kuollut yhteensä {value} henkilöä [{time}]
fi-head: yhteensä {value} COVID-19 kuolemaa {where, case=ssa} [{time}]
| value_type = Latest:Deaths:Total
"""


class LatestDeathsTotalInCountryResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, data: CountryData, context: List[CountryData]) -> List[Message]:

        latest = data.observations[-1]

        return [
            Message(
                Fact(
                    "[ENTITY:COUNTRY:{}]".format(data.country),
                    "country",
                    latest.timestamp,
                    "date_by",
                    latest.deaths,
                    "Latest:Deaths:Total",
                    1,
                )
            )
        ]

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return []
