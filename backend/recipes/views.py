from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from .models import Recipe


def extract_from_short_url(request, recipe_id):
    get_object_or_404(Recipe, id=recipe_id)
    return redirect(f'/recipes/{recipe_id}/')
