from django.shortcuts import redirect
from .models import Recipe


def extract_from_short_url(request, recipe_id=None):
    recipe = Recipe.objects.get(id=recipe_id)
    return redirect(f'/recipes/{recipe.id}/')
