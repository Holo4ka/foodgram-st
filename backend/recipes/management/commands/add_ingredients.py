import json
from recipes.models import Ingredient
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Заполняет базу данных ингредиентами'

    def handle(self, *args, **kwargs):
        try:
            with open('././ingredients.json', encoding='utf-8') as f:
                data = json.load(f)
            created_objects = Ingredient.objects.bulk_create(
                [Ingredient(**item) for item in data], ignore_conflicts=True)
            self.stdout.write(f'Количество добавленных ингредиентов - {len(created_objects)}')
        except Exception as e:
            self.stderr.write(f'Ошибка при обработке файла ingredients.json: {e}')
