import json
from recipes.models import Ingredient
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Заполняет базу данных ингредиентами'

    def handle(self, *args, **kwargs):
        with open('././ingredients.json', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                Ingredient.objects.create(**item)
