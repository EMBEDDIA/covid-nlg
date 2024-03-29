import logging
import random
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Tuple

import requests
from cachetools import TTLCache, cached

from coronabot.resources.latest_confirmed_daily_change_in_country_resource import (
    LatestConfirmedDailyChangeInCountryResource,
)
from coronabot.resources.latest_confirmed_weekly_change_in_country_resource import (
    LatestConfirmedWeeklyChangeInCountryResource,
)
from coronabot.resources.latest_deaths_daily_change_in_country_resource import LatestDeathsDailyChangeInCountryResource
from coronabot.resources.latest_deaths_total_in_country_resource import LatestDeathsTotalInCountryResource
from coronabot.resources.latest_deaths_weekly_change_in_country_resource import (
    LatestDeathsWeeklyChangeInCountryResource,
)
from coronabot.resources.latest_recovered_daily_change_in_country_resource import (
    LatestRecoveredDailyChangeInCountryResource,
)
from coronabot.resources.latest_recovered_total_in_country_resource import LatestRecoveredTotalInCountryResource
from coronabot.resources.latest_recovered_weekly_change_in_country_resource import (
    LatestRecoveredWeeklyChangeInCountryResource,
)
from coronabot.resources.time_resource import TimeResource
from coronabot.resources.latest_data_from_resource import LatestDataFromResource

from .constants import CONJUNCTIONS, get_error_message
from .core.aggregator import Aggregator
from .core.document_planner import NoInterestingMessagesException
from .core.models import Template
from .core.morphological_realizer import MorphologicalRealizer
from .core.pipeline import NLGPipeline, NLGPipelineComponent
from .core.realize_slots import SlotRealizer
from .core.registry import Registry
from .core.surface_realizer import BodyHTMLSurfaceRealizer, HeadlineHTMLSurfaceRealizer
from .core.template_reader import read_templates
from .core.template_selector import TemplateSelector
from .corona_document_planner import CoronaBodyDocumentPlanner, CoronaHeadlineDocumentPlanner
from .corona_importance_allocator import CoronaImportanceSelector
from .corona_message_generator import CoronaMessageGenerator, NoMessagesForSelectionException
from .corona_named_entity_resolver import CoronaEntityNameResolver
from .english_uralicNLP_morphological_realizer import EnglishUralicNLPMorphologicalRealizer
from .finnish_uralicNLP_morphological_realizer import FinnishUralicNLPMorphologicalRealizer
from .resources.latest_confirmed_total_in_country_resource import LatestConfirmedTotalInCountryResource
from .resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


class CoronaNlgService(object):

    processor_resources: List[ProcessorResource] = []

    # These are (re)initialized every time run_pipeline is called
    body_pipeline = None
    headline_pipeline = None

    def __init__(self, random_seed: int = None) -> None:
        """
        :param random_seed: seed for random number generation, for repeatability
        """

        # New registry and result importer
        self.registry = Registry()

        # Per-processor resources
        self.processor_resources = [
            TimeResource(),
            LatestConfirmedTotalInCountryResource(),
            LatestDeathsTotalInCountryResource(),
            LatestRecoveredTotalInCountryResource(),
            LatestConfirmedDailyChangeInCountryResource(),
            LatestDeathsDailyChangeInCountryResource(),
            LatestRecoveredDailyChangeInCountryResource(),
            LatestConfirmedWeeklyChangeInCountryResource(),
            LatestDeathsWeeklyChangeInCountryResource(),
            LatestRecoveredWeeklyChangeInCountryResource(),
            LatestDataFromResource(),
        ]

        # Templates
        self.registry.register("templates", self._load_templates())

        # Misc language data
        self.registry.register("CONJUNCTIONS", CONJUNCTIONS)

        # PRNG seed
        self._set_seed(seed_val=random_seed)

        # Message Parsers
        self.registry.register("message-parsers", [])
        for processor_resource in self.processor_resources:
            self.registry.get("message-parsers").append(processor_resource.parse_messages)

        # Slot Realizers Components
        self.registry.register("slot-realizers", [])
        for processor_resource in self.processor_resources:
            components = [component(self.registry) for component in processor_resource.slot_realizer_components()]
            self.registry.get("slot-realizers").extend(components)

    def _load_templates(self) -> Dict[str, List[Template]]:
        log.info("Loading templates")
        templates: Dict[str, List[Template]] = defaultdict(list)
        for resource in self.processor_resources:
            for language, new_templates in read_templates(resource.templates_string())[0].items():
                templates[language].extend(new_templates)
        return templates

    def _get_components(self, type: str) -> Iterable[NLGPipelineComponent]:
        yield CoronaMessageGenerator()
        yield CoronaImportanceSelector()

        if type == "headline":
            yield CoronaHeadlineDocumentPlanner()
        else:
            yield CoronaBodyDocumentPlanner()

        yield TemplateSelector()
        yield Aggregator()
        yield SlotRealizer()
        yield CoronaEntityNameResolver()

        yield MorphologicalRealizer(
            {"fi": FinnishUralicNLPMorphologicalRealizer(), "en": EnglishUralicNLPMorphologicalRealizer()}
        )

        if type == "headline":
            yield HeadlineHTMLSurfaceRealizer()
        else:
            yield BodyHTMLSurfaceRealizer()

    def run_pipeline(self, language: str, location: str) -> Tuple[str, str, List[str]]:
        log.info("Configuring Body NLG Pipeline")
        self.body_pipeline = NLGPipeline(self.registry, *self._get_components("body"))
        self.headline_pipeline = NLGPipeline(self.registry, *self._get_components("headline"))

        errors: List[str] = []

        log.info("Running headline NLG pipeline")
        try:
            headline_lang = "{}-head".format(language)
            headline = self.headline_pipeline.run((location,), headline_lang, prng_seed=self.registry.get("seed"))
            log.info("Headline pipeline complete")
        except NoMessagesForSelectionException as ex:
            log.error("%s", ex)
            headline = get_error_message(language, "no-messages-for-selection")
            errors.append("NoMessagesForSelectionException")
        except NoInterestingMessagesException as ex:
            log.info("%s", ex)
            headline = get_error_message(language, "no-interesting-messages-for-selection")
            errors.append("NoInterestingMessagesException")
        except Exception as ex:
            log.exception("%s", ex)
            headline = get_error_message(language, "general-error")
            errors.append("{}: {}".format(ex.__class__.__name__, str(ex)))

        log.info("Running Body NLG pipeline: language={}".format(language))
        try:
            body = self.body_pipeline.run((location,), language, prng_seed=self.registry.get("seed"))
            log.info("Body pipeline complete")
        except NoMessagesForSelectionException as ex:
            log.error("%s", ex)
            body = get_error_message(language, "no-messages-for-selection")
            errors.append("NoMessagesForSelectionException")
        except NoInterestingMessagesException as ex:
            log.info("%s", ex)
            body = get_error_message(language, "no-interesting-messages-for-selection")
            errors.append("NoInterestingMessagesException")
        except Exception as ex:
            log.exception("%s", ex)
            body = get_error_message(language, "general-error")
            errors.append("{}: {}".format(ex.__class__.__name__, str(ex)))

        return headline, body, errors

    def _set_seed(self, seed_val: Optional[int] = None) -> None:
        log.info("Selecting seed for NLG pipeline")
        if not seed_val:
            seed_val = random.randint(1, 10000000)
            log.info("No preset seed, using random seed {}".format(seed_val))
        else:
            log.info("Using preset seed {}".format(seed_val))
        self.registry.register("seed", seed_val)

    def get_languages(self) -> List[str]:
        return list(self.registry.get("templates").keys())

    @cached(cache=TTLCache(maxsize=1, ttl=900))  # Cache for 15 minutes.
    def get_locations(self) -> List[str]:
        return list(requests.get("https://pomber.github.io/covid19/timeseries.json").json().keys())
