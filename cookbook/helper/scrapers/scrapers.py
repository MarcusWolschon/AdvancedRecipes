from bs4 import BeautifulSoup
from json import JSONDecodeError
from recipe_scrapers import SCRAPERS, get_host_name
from recipe_scrapers._factory import SchemaScraperFactory
from recipe_scrapers._schemaorg import SchemaOrg

from .cooksillustrated import CooksIllustrated

# vvvvvvvvvvvvvvvvvvvvvv
from gettext import gettext as _
from recipes import settings
from .cookidoo import Cookidoo
import re
# ^^^^^^^^^^^^^^^^^^^^^^

CUSTOM_SCRAPERS = {
    CooksIllustrated.host(site="cooksillustrated"): CooksIllustrated,
    CooksIllustrated.host(site="americastestkitchen"): CooksIllustrated,
    CooksIllustrated.host(site="cookscountry"): CooksIllustrated,

    # vvvvvvvvvvvvvvvvvvvvvv
    "cookidoo.de": Cookidoo,
    "cookidoo.at": Cookidoo,
    "cookidoo.ch": Cookidoo,
    # ^^^^^^^^^^^^^^^^^^^^^^

}
SCRAPERS.update(CUSTOM_SCRAPERS)


def text_scraper(text, url=None):
    domain = None
    if url:
        domain = get_host_name(url)
    if domain in SCRAPERS:
        scraper_class = SCRAPERS[domain]
    else:
        scraper_class = SchemaScraperFactory.SchemaScraper

    class TextScraper(scraper_class):
        def __init__(
            self,
            page_data,
            url=None
        ):
            self.wild_mode = False
            self.meta_http_equiv = False
            self.soup = BeautifulSoup(page_data, "html.parser")
            self.url = url
            self.recipe = None
            try:
                self.schema = SchemaOrg(page_data)
            except (JSONDecodeError, AttributeError):
                pass

        # vvvvvvvvvvvvvvvvvvvvvv
        def normalize_instruction(self, instruction):
            if instruction is None:
                return ""
            time = "(Zeit gemäß Packungsangabe|\d+ ([Ss]e[kc]|[Mm]in))"
            temperature = "(/\d+°C)?"
            reverse = "(/|/Linkslauf)?"
            speed = "(Stufe \d+|Stufe |)"
            full = time + "\.?" + temperature + reverse + "/" + speed
            return re.sub("(" + full + ")", "**\\1**", instruction) \
                .replace("", _('Linkslauf')) \
                .replace("", _('Kochlöffel')) \
                .replace("", _('Kneten')) \
                .replace("Rühraufsatz einsetzen", "**Rühraufsatz einsetzen**") \
                .replace("Rühraufsatz entfernen", "**Rühraufsatz entfernen**")


        def instructions(self):
            instructions = self.schema.data.get("recipeInstructions") or ""

            if settings.DEBUG:
                print("TextScraper: parsing instructions of type " + instructions.__class__.__name__)

            # handle block of text in format "1.step1...\n2.step2....\n..."
            if isinstance(instructions, str):
                if settings.DEBUG:
                    print("TextScraper: before=" + instructions)
                instructions = re.split('\\\n\\d+\\.', instructions)
                if settings.DEBUG:
                    print("TextScraper: string instructions broken up into " + str(len(instructions)) + " steps")

            # handle instructions already presented as steps
            if isinstance(instructions, list):
                if settings.DEBUG:
                    print("TextScraper: parsing instruction")
                instructions_gist = []
                step_number = 1
                for schema_instruction_item in instructions:
                    instructions_gist += self.extract_instructions_text(schema_instruction_item, "#", step_number)
                    step_number = step_number + 1

                # add "header 1" or "header 2" markdown to marks the beginning of a new step
                return "".join(self.normalize_instruction(instruction)
                               for instruction in instructions_gist)

            return instructions

        def extract_instructions_text(self, schema_item, prefix, start_step_number):
            step_number = start_step_number
            step_format = "\n\n" + prefix + _("Step {}") + "\n\n{}"
            section_format = "\n\n{}\n\n"
            instructions_gist = []

            if type(schema_item) is str:
                if settings.DEBUG:
                    print("TextScraper: instruction is string")
                instructions_gist.append(step_format.format(step_number, schema_item))
                step_number = step_number + 1
            elif schema_item.get("@type") == "HowToStep":
                if settings.DEBUG:
                    print("TextScraper: instruction is HowToStep")
                if schema_item.get("name", False):
                    # some sites have duplicated name and text properties (1:1)
                    # others have name same as text but truncated to X chars.
                    # ignore name in these cases and add the name value only if it's different from the text
                    if not schema_item.get("text").startswith(
                            schema_item.get("name").rstrip(".")
                    ):
                        instructions_gist.append(step_format.format(step_number, schema_item.get("name")))
                instructions_gist.append(step_format.format(step_number, schema_item.get("text")))
            elif schema_item.get("@type") == "HowToSection":
                if settings.DEBUG:
                    print("TextScraper: instruction is HowToSection")
                section_name = schema_item.get("name") or schema_item.get("Name") or _("Instructions")
                instructions_gist.append(section_format.format(section_name))
                step_number = 1
                for item in schema_item.get("itemListElement"):
                    instructions_gist += self.extract_instructions_text(item, "#" + prefix, step_number)
                    step_number = step_number + 1
            return instructions_gist
        # ^^^^^^^^^^^^^^^^^^^^^^

    return TextScraper(text, url)
