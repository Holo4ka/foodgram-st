from django.shortcuts import redirect


def extract_from_short_url(request, recipe_id):
    return redirect(f'/recipes/{recipe_id}/')
