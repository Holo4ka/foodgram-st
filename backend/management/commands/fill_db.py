import json
from recipes.models import Recipe

with open('path/to/your_file.json', encoding='utf-8') as f:
    data = json.load(f)
    for item in data:
        Recipe.objects.create(**item)
