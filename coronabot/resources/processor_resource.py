from abc import ABC, abstractmethod
from typing import List, Type

from ..core.models import Message
from ..core.realize_slots import SlotRealizerComponent
from ..corona_message_generator import CountryData


class ProcessorResource(ABC):

    EPSILON = 0.00000001

    @abstractmethod
    def templates_string(self) -> str:
        pass

    @abstractmethod
    def parse_messages(self, task_result: CountryData, context: List[CountryData]) -> List[Message]:
        pass

    @abstractmethod
    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        pass
