import json
import uuid
from datetime import datetime
from io import BytesIO

import requests
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.db.transaction import atomic
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django_tables2 import RequestConfig
from PIL import UnidentifiedImageError
from requests.exceptions import MissingSchema

from cookbook.forms import BatchEditForm, SyncForm
from cookbook.helper.image_processing import handle_image
from cookbook.helper.ingredient_parser import IngredientParser
from cookbook.helper.permission_helper import group_required, has_group_permission
from cookbook.helper.recipe_url_import import parse_cooktime
from cookbook.models import (Comment, Food, Ingredient, Keyword, Recipe, RecipeImport, Step, Sync,
                             Unit, UserPreference)
from cookbook.tables import SyncTable
from recipes import settings

# vvvvvvvvvvvvvvvvvvvvvv
import re
from cookbook.models import (NutritionInformation)
# ^^^^^^^^^^^^^^^^^^^^^^


@group_required('user')
def sync(request):
    if request.space.max_recipes != 0 and Recipe.objects.filter(space=request.space).count() >= request.space.max_recipes:  # TODO move to central helper function
        messages.add_message(request, messages.WARNING, _('You have reached the maximum number of recipes for your space.'))
        return HttpResponseRedirect(reverse('index'))

    if request.space.max_users != 0 and UserPreference.objects.filter(space=request.space).count() > request.space.max_users:
        messages.add_message(request, messages.WARNING, _('You have more users than allowed in your space.'))
        return HttpResponseRedirect(reverse('index'))

    if request.space.demo or settings.HOSTED:
        messages.add_message(request, messages.ERROR, _('This feature is not yet available in the hosted version of tandoor!'))
        return redirect('index')

    if request.method == "POST":
        if not has_group_permission(request.user, ['admin']):
            messages.add_message(request, messages.ERROR, _('You do not have the required permissions to view this page!'))
            return HttpResponseRedirect(reverse('data_sync'))
        form = SyncForm(request.POST, space=request.space)
        if form.is_valid():
            new_path = Sync()
            new_path.path = form.cleaned_data['path']
            new_path.storage = form.cleaned_data['storage']
            new_path.last_checked = datetime.now()
            new_path.space = request.space
            new_path.save()
            return redirect('data_sync')
    else:
        form = SyncForm(space=request.space)

    monitored_paths = SyncTable(Sync.objects.filter(space=request.space).all())
    RequestConfig(request, paginate={'per_page': 25}).configure(monitored_paths)

    return render(request, 'batch/monitor.html', {'form': form, 'monitored_paths': monitored_paths})


@group_required('user')
def sync_wait(request):
    return render(request, 'batch/waiting.html')


@group_required('user')
def batch_import(request):
    imports = RecipeImport.objects.filter(space=request.space).all()
    for new_recipe in imports:
        recipe = Recipe(
            name=new_recipe.name,
            file_path=new_recipe.file_path,
            storage=new_recipe.storage,
            file_uid=new_recipe.file_uid,
            created_by=request.user,
            space=request.space
        )
        recipe.save()
        new_recipe.delete()

    return redirect('list_recipe_import')


@group_required('user')
def batch_edit(request):
    if request.method == "POST":
        form = BatchEditForm(request.POST, space=request.space)
        if form.is_valid():
            word = form.cleaned_data['search']
            keywords = form.cleaned_data['keywords']

            recipes = Recipe.objects.filter(name__icontains=word, space=request.space)
            count = 0
            for recipe in recipes:
                edit = False
                if keywords.__sizeof__() > 0:
                    recipe.keywords.add(*list(keywords))
                    edit = True
                if edit:
                    count = count + 1

                recipe.save()

            msg = ngettext(
                'Batch edit done. %(count)d recipe was updated.',
                'Batch edit done. %(count)d Recipes where updated.',
                count) % {
                'count': count,
            }
            messages.add_message(request, messages.SUCCESS, msg)

            return redirect('data_batch_edit')
    else:
        form = BatchEditForm(space=request.space)

    return render(request, 'batch/edit.html', {'form': form})


@group_required('user')
@atomic
def import_url(request):
    if request.space.max_recipes != 0 and Recipe.objects.filter(space=request.space).count() >= request.space.max_recipes:  # TODO move to central helper function
        messages.add_message(request, messages.WARNING, _('You have reached the maximum number of recipes for your space.'))
        return HttpResponseRedirect(reverse('index'))

    if request.space.max_users != 0 and UserPreference.objects.filter(space=request.space).count() > request.space.max_users:
        messages.add_message(request, messages.WARNING, _('You have more users than allowed in your space.'))
        return HttpResponseRedirect(reverse('index'))

    if request.method == 'POST':
        data = json.loads(request.body)
        data['cookTime'] = parse_cooktime(data.get('cookTime', ''))
        data['prepTime'] = parse_cooktime(data.get('prepTime', ''))

        # vvvvvvvvvvvvvvvvvvvvvv
        calories = 0
        carbohydrates = 0
        fats = 0
        proteins = 0

        if data['nutrition']:
            if 'calories' in data['nutrition']:
                calories = data['nutrition']['calories']
            if 'carbohydrates' in data['nutrition']:
                carbohydrates = data['nutrition']['carbohydrates']
            if 'fats' in data['nutrition']:
                fats = data['nutrition']['fats']
            if 'proteins' in data['nutrition']:
                proteins = data['nutrition']['proteins']

        if settings.DEBUG:
            print("data.py calories=" + str(calories))
            print("data.py carbohydrates=" + str(carbohydrates))
            print("data.py fats=" + str(fats))
            print("data.py proteins=" + str(proteins))

        if data['nutrition_per_serving']:
            servings = float(data['servings'])
            calories = float(calories) * servings
            carbohydrates = float(carbohydrates) * servings
            fats = float(fats) * servings
            proteins = float(proteins) * servings
            if settings.DEBUG:
                print("data.py servings=" + str(servings))
                print("data.py total calories=" + str(calories))
                print("data.py total carbohydrates=" + str(carbohydrates))
                print("data.py total fats=" + str(fats))
                print("data.py total proteins=" + str(proteins))

        nutrition = NutritionInformation.objects.create(
            calories=calories,
            carbohydrates=carbohydrates,
            fats=fats,
            proteins=proteins,
            source=data['nutrition']['source'],
            space=request.space,
        )
        # ^^^^^^^^^^^^^^^^^^^^^^

        recipe = Recipe.objects.create(
            name=data['name'],
            description=data['description'],
            waiting_time=data['cookTime'],
            working_time=data['prepTime'],
            servings=data['servings'],
            internal=True,
            created_by=request.user,
            space=request.space,
            nutrition=nutrition,   # <<<<<<<<<<<<<<<<<<<<
        )
        """

        step = Step.objects.create(
            instruction=data['recipeInstructions'], space=request.space,
        )

        recipe.steps.add(step)


        """
        # vvvvvvvvvvvvvvvvvvvvvv
        steps = []
        if data['import_as_steps']:
            if settings.DEBUG:
                print("data.py importing separate steps")
            # split steps by header 1 markdown annotations
            instructions = re.split('(#[^\n]+)', data['recipeInstructions'])
            next_step_name = ""
            for instruction in instructions:
                if not instruction.strip():
                    if settings.DEBUG:
                        print("data.py ignoring empty step")
                    continue
                if instruction.startswith('#'):
                    found = next_step_name = instruction[1:]
                    if len(next_step_name) == 0:
                        if settings.DEBUG:
                            print("data.py two step names, importing as section " + found)
                        new_step = Step.objects.create(name=next_step_name.strip(), instruction=instruction.strip(), space=request.space, show_as_header=True)
                        steps.append(new_step)
                        new_step.save()
                        recipe.steps.add(new_step)
                    next_step_name = found
                    if settings.DEBUG:
                        print("data.py found step name " + next_step_name)
                else:
                    if settings.DEBUG:
                        print("data.py found instructions, importing step name " + next_step_name)
                    new_step = Step.objects.create(name=next_step_name.strip(), instruction=instruction.strip(), space=request.space, show_as_header=False)
                    next_step_name = ""
                    steps.append(new_step)
                    new_step.save()
                    recipe.steps.add(new_step)
        else:
            new_step = Step.objects.create(
                instruction=data['recipeInstructions'], space=request.space,
            )
            steps.append(new_step)
            new_step.save()
            recipe.steps.add(new_step)
        # ^^^^^^^^^^^^^^^^^^^^^^

        for kw in data['keywords']:
            # vvvvvvvvvvvvvvvvvvvvvv
            if not kw['text'].strip():
                # ignore blank keywords
                continue
            # ^^^^^^^^^^^^^^^^^^^^^^
            if data['all_keywords']: # do not remove this check :) https://github.com/vabene1111/recipes/issues/645
                k, created = Keyword.objects.get_or_create(name=kw['text'], space=request.space)
                recipe.keywords.add(k)
            else:
                try:
                    k = Keyword.objects.get(name=kw['text'], space=request.space)
                    recipe.keywords.add(k)
                except ObjectDoesNotExist:
                    pass

        ingredient_parser = IngredientParser(request, True)
        for ing in data['recipeIngredient']:
            ingredient = Ingredient(space=request.space, )

            if food_text := ing['ingredient']['text'].strip():
                ingredient.food = ingredient_parser.get_food(food_text)

            if ing['unit']:
                if unit_text := ing['unit']['text'].strip():
                    ingredient.unit = ingredient_parser.get_unit(unit_text)

            # TODO properly handle no_amount recipes
            if isinstance(ing['amount'], str):
                try:
                    ingredient.amount = float(ing['amount'].replace(',', '.'))
                except ValueError:
                    ingredient.no_amount = True
                    pass
            elif isinstance(ing['amount'], float) \
                    or isinstance(ing['amount'], int):
                ingredient.amount = ing['amount']
            ingredient.note = ing['note'].strip() if 'note' in ing else ''

            ingredient.save()

            # vvvvvvvvvvvvvvvvvvvvvv
            step = find_step_for_ingredient(steps, ingredient)
            # ^^^^^^^^^^^^^^^^^^^^^^

            step.ingredients.add(ingredient)

        if 'image' in data and data['image'] != '' and data['image'] is not None:
            try:
                response = requests.get(data['image'])

                img, filetype = handle_image(request, File(BytesIO(response.content), name='image'))
                recipe.image = File(
                    img, name=f'{uuid.uuid4()}_{recipe.pk}{filetype}'
                )
                recipe.save()
            except UnidentifiedImageError as e:
                print(e)
                pass
            except MissingSchema as e:
                print(e)
                pass
            except Exception as e:
                print(e)
                pass

        return HttpResponse(reverse('view_recipe', args=[recipe.pk]))

    if 'id' in request.GET:
        context = {'bookmarklet': request.GET.get('id', '')}
    else:
        context = {}

    return render(request, 'url_import.html', context)

# vvvvvvvvvvvvvvvvvvvvvv
def find_step_for_ingredient(steps, ingredient):
    for step in steps:
        if ingredient.food.name in step.instruction:
            return step
    return steps[0]
# ^^^^^^^^^^^^^^^^^^^^^^

class Object(object):
    pass


@group_required('user')
def statistics(request):
    counts = Object()
    counts.recipes = Recipe.objects.filter(space=request.space).count()
    counts.keywords = Keyword.objects.filter(space=request.space).count()
    counts.recipe_import = RecipeImport.objects.filter(space=request.space).count()
    counts.units = Unit.objects.filter(space=request.space).count()
    counts.ingredients = Food.objects.filter(space=request.space).count()
    counts.comments = Comment.objects.filter(recipe__space=request.space).count()

    counts.recipes_internal = Recipe.objects.filter(internal=True, space=request.space).count()
    counts.recipes_external = counts.recipes - counts.recipes_internal

    counts.recipes_no_keyword = Recipe.objects.filter(keywords=None, space=request.space).count()

    return render(request, 'stats.html', {'counts': counts})
