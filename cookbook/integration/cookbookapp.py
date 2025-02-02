import base64
import gzip
import json
import re
from io import BytesIO

import requests
import yaml

from cookbook.helper.ingredient_parser import IngredientParser
from cookbook.helper.recipe_html_import import get_recipe_from_source
from cookbook.helper.recipe_url_import import iso_duration_to_minutes
from cookbook.integration.integration import Integration
from cookbook.models import Recipe, Step, Ingredient, Keyword
from gettext import gettext as _

# vvvvvvvvvvvvvvvvvvvvvv
from recipes import settings
# ^^^^^^^^^^^^^^^^^^^^^^

class CookBookApp(Integration):

    def import_file_name_filter(self, zip_info_object):
        return zip_info_object.filename.endswith('.html')

    def get_recipe_from_file(self, file):
        recipe_html = file.getvalue().decode("utf-8")

        recipe_json, recipe_tree, html_data, images = get_recipe_from_source(recipe_html, 'CookBookApp', self.request)

        recipe = Recipe.objects.create(
            name=recipe_json['name'].strip(),
            created_by=self.request.user, internal=True,
            space=self.request.space)

        try:
            recipe.servings = re.findall('([0-9])+', recipe_json['recipeYield'])[0]
        except Exception as e:
            pass

        try:
            recipe.working_time = iso_duration_to_minutes(recipe_json['prepTime'])
            recipe.waiting_time = iso_duration_to_minutes(recipe_json['cookTime'])
        except Exception:
            pass

        step = Step.objects.create(instruction=recipe_json['recipeInstructions'], space=self.request.space, )

        # vvvvvvvvvvvvvvvvvvvvvv
        if 'nutrients' in recipe_json:
            if settings.DEBUG:
                print("found nutrient")
            calories = 0
            carbohydrates = 0
            fats = 0
            proteins = 0
            if 'calories' in recipe_json['nutrition']:
                calories = remove_non_digts(recipe_json['nutrition']['calories'])
            if 'carbohydrateContent' in recipe_json['nutrition']:
                carbohydrates = remove_non_digts(recipe_json['nutrition']['carbohydrateContent'])
            if 'fatContent' in recipe_json['nutrition']:
                fats = remove_non_digts(recipe_json['nutrition']['fatContent'])
            if 'proteinContent' in recipe_json['nutrition']:
                proteins = remove_non_digts(recipe_json['nutrition']['proteinContent'])

            recipe.nutrition = NutritionInformation.objects.create(
                calories=calories,
                carbohydrates=carbohydrates,
                fats=fats,
                proteins=proteins,
                source='cookbookapp',
                space=self.request.space,
            )
        # ^^^^^^^^^^^^^^^^^^^^^^

        step.save()
        recipe.steps.add(step)

        ingredient_parser = IngredientParser(self.request, True)
        for ingredient in recipe_json['recipeIngredient']:
                f = ingredient_parser.get_food(ingredient['ingredient']['text'])
                u = ingredient_parser.get_unit(ingredient['unit']['text'])
                step.ingredients.add(Ingredient.objects.create(
                    food=f, unit=u, amount=ingredient['amount'], note=ingredient['note'], space=self.request.space,
                ))

        if len(images) > 0:
            try:
                response = requests.get(images[0])
                self.import_recipe_image(recipe, BytesIO(response.content))
            except Exception as e:
                print('failed to import image ', str(e))

        recipe.save()
        return recipe

    # remove everything that is not part of the first, english, decimal number
    def remove_non_digts(input):
        match = re.search('\d+\.?\d*', input)
        if match:
            return match.group()
        else:
            return ""
