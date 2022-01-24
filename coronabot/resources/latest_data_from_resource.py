import logging
from typing import List, Type

from ..core.models import Fact, Message
from ..core.realize_slots import SlotRealizerComponent
from ..corona_message_generator import CountryData
from .processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: the data for {where} was last updated {time}
fi: {where, case=gen} uusimmat tiedot on päivitetty {time}
| value_type = DataFrom:Latest

en: the second to last update was on {time}
fi: toiseksi viimeisin päivitys tapahtui {time}
| value_type = DataFrom:Previous
"""


class LatestDataFromResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, data: CountryData, context: List[CountryData]) -> List[Message]:
        latest = data.observations[-1]
        second_to_last = data.observations[-2]

        messages = [
            Message(
                Fact(
                    "[ENTITY:COUNTRY:{}]".format(data.country),
                    "country",
                    str(latest.timestamp),
                    "date",
                    0,
                    "DataFrom:Latest",
                    2,
                )
            ),
            Message(
                Fact(
                    "[ENTITY:COUNTRY:{}]".format(data.country),
                    "country",
                    str(second_to_last.timestamp),
                    "date",
                    0,
                    "DataFrom:Previous",
                    1.9,
                )
            ),
        ]
        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return []
