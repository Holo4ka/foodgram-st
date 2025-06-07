import json
from recipes.models import Ingredient
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Заполняет базу данных ингредиентами'

    def handle(self, *args, **kwargs):
        try:
            with open('././ingredients.json', encoding='utf-8') as f:
                data = json.load(f)
            ingredients = [Ingredient(**item) for item in data]
            Ingredient.objects.bulk_create(ingredients, ignore_conflicts=True)
        except FileNotFoundError:
            self.stderr.write("Файл не найден.")
            return
        except json.JSONDecodeError as e:
            self.stderr.write(f"Ошибка разбора JSON: {e}")
            return
        except TypeError as e:
            self.stderr.write(f"Ошибка структуры данных: {e}")
