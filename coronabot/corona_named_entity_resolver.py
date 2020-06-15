import datetime
import logging
import re
from typing import Dict, Tuple

from numpy.random import Generator

from coronabot.resources.time_resource import DATE_EXPRESSIONS, DateFormat
from coronabot.resources.country_resource import COUNTRY_NAMES

from .core.entity_name_resolver import EntityNameResolver
from .core.models import Slot
from .core.registry import Registry

log = logging.getLogger("root")


class CoronaEntityNameResolver(EntityNameResolver):
    def __init__(self) -> None:
        # [ENTITY:<group1>:<group2>] where group1 and group2 can contain anything but square brackets or double colon
        self._matcher = re.compile(r"\[ENTITY:([^\]:]*):([^\]]*)\]")

    def is_entity(self, maybe_entity: str) -> bool:
        # Match and convert the result to boolean
        try:
            return self._matcher.fullmatch(maybe_entity) is not None
        except TypeError:
            log.error("EntityNameResolver got a number: {} instead of a string".format(maybe_entity))

    def parse_entity(self, entity: str) -> Tuple[str, str]:
        groups: Tuple[str, str] = tuple(self._matcher.match(entity).groups())
        assert len(groups) == 2
        return tuple(groups)

    def resolve_surface_form(
        self, registry: Registry, random: Generator, language: str, slot: Slot, entity: str, entity_type: str
    ) -> None:
        if entity_type == "COUNTRY":
            value = self._resolve_country(entity, COUNTRY_NAMES.get(language.split("-")[0], {}))
        elif entity_type == "DATE":
            value = self._resolve_date(entity, DATE_EXPRESSIONS.get(language.split("-")[0], {}))
        else:
            return
        # Was one of the matching things
        slot.value = lambda f: value

    def _resolve_date(self, entity: str, date_expressions: Dict[DateFormat, str]) -> str:
        log.debug("Entity is date, resolving")
        today = datetime.date.today()
        entity_year, entity_month, entity_day = (int(component) for component in entity.split("-"))
        entity_date = datetime.date(entity_year, entity_month, entity_day)

        date_delta = (today - entity_date).days
        log.debug("Entity is {}, delta from today is {}".format(entity_date, date_delta))

        if date_delta in (date_format[1].value for date_format in DateFormat.__members__.items()):
            log.debug("Retrieving from expression dict")
            return date_expressions.get(DateFormat(date_delta), entity)
        else:
            log.debug("Delta not in expression dict, returning as-is")
            return entity

    def _resolve_country(self, entity: str, country_expressions: Dict[str, str]) -> str:
        log.debug("Entity {} is a country, resolving".format(entity))
        if entity not in country_expressions:
            log.error("Unknown country, returning as-is")
            return entity
        resolved_form = country_expressions.get(entity)
        log.debug("Resolved as {}".format(resolved_form))
        return resolved_form
