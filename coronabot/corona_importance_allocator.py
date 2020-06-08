import logging
from typing import List, Tuple

from numpy.random import Generator

from .core.models import Message
from .core.pipeline import NLGPipelineComponent, Registry

log = logging.getLogger("root")


class CoronaImportanceSelector(NLGPipelineComponent):
    def run(
        self, registry: Registry, random: Generator, language: str, messages: List[Message], location: str
    ) -> Tuple[List[Message]]:
        """
        Runs this pipeline component.
        """
        facts = messages
        scored_messages = self.score_importance(facts, location)
        sorted_scored_messages = sorted(scored_messages, key=lambda x: float(x.score), reverse=True)
        return (sorted_scored_messages,)

    def score_importance(self, messages: List[Message], location: str) -> List[Message]:
        for msg in messages:
            msg.score = self.score_importance_single(msg, location)
        return messages

    def score_importance_single(self, message: Message, location: str) -> float:
        if message.main_fact.where_type == "country" and message.main_fact.where != location:
            log.info(
                "INCORRECT COUNTRY: {} {}, expected {}".format(
                    message.main_fact.where_type, message.main_fact.where, location
                )
            )
            return 0
        return message.main_fact.outlierness
