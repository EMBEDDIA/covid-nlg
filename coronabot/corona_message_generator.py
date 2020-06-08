import logging
import requests
from datetime import date
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from cachetools import TTLCache, cached
from numpy.random import Generator

from .core.message_generator import NoMessagesForSelectionException
from .core.models import Message
from .core.pipeline import NLGPipelineComponent, Registry

log = logging.getLogger("root")


class Observation:
    def __init__(self, timestamp: date, confirmed: int, deaths: int, recovered: Optional[int]) -> None:
        self.timestamp = timestamp
        self.confirmed = confirmed
        self.deaths = deaths
        self.recovered = recovered

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> "Observation":
        return Observation(
            date(*(int(x) for x in dict.get("date").split("-"))),
            int(dict.get("confirmed")),
            int(dict.get("deaths")),
            int(dict.get("recovered")) if dict.get("recovered") else None,
        )


class CountryData:
    def __init__(self, country: str, observations: List[Observation],) -> None:
        self.country = country
        self.observations = observations

    @staticmethod
    def from_dict(country: str, observations: List[Dict[str, Union[int, str]]]) -> "CountryData":
        return CountryData(country, [Observation.from_dict(observation) for observation in observations])


class CoronaMessageGenerator(NLGPipelineComponent):
    @cached(cache=TTLCache(maxsize=1, ttl=900))  # Cache for 15 minutes.
    def _load_data(self) -> Dict[str, List[Dict[str, Union[int, str]]]]:
        return requests.get("https://pomber.github.io/covid19/timeseries.json").json()

    def run(self, registry: Registry, random: Generator, language: str, location: str) -> Tuple[List[Message], str]:
        """
        Run this pipeline component.
        """
        message_parsers: List[Callable[[CountryData, List[CountryData]], List[Message]]] = registry.get(
            "message-parsers"
        )

        data: Dict[str, List[str : Union[int, str]]] = self._load_data()
        if not data:
            raise NoMessagesForSelectionException("No data at all!")

        countries: List[CountryData] = [
            CountryData.from_dict(country, time_series) for country, time_series in data.items()
        ]

        messages: List[Message] = []
        for country in countries:
            generation_succeeded = False
            for message_parser in message_parsers:
                try:
                    new_messages = message_parser(country, countries)
                    for message in new_messages:
                        log.debug("Parsed message {}".format(message))
                    if new_messages:
                        generation_succeeded = True
                        messages.extend(new_messages)
                except Exception as ex:
                    log.error("Message parser crashed: {}".format(ex), exc_info=True)

            if not generation_succeeded:
                log.error("Failed to parse a Message from {}".format(country))

        # Filter out messages that share the same underlying fact. Can't be done with set() because of how the
        # __hash__ and __eq__ are (not) defined.
        facts = set()
        uniq_messages = []
        for m in messages:
            if m.main_fact not in facts:
                facts.add(m.main_fact)
                uniq_messages.append(m)
        messages = uniq_messages

        if not messages:
            raise NoMessagesForSelectionException()

        return (
            messages,
            location,
        )
