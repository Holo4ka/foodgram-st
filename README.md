# Проект FOODGRAM

Автор - Борин Игорь Михайлович
https://t.me/Holoforka

Технологии, использованные в проекте:
Python
Django, Django Rest Framework, djoser
База данных: PostgreSQL
Nginx, Gunicorn
Docker


## Запуск проекта:
Клонировать репозиторий:

```git clone https://github.com/Holo4ka/foodgram-st.git```

```cd foodgram-st```


Создать файл .env:
```cp .env.example .env```

```echo "DJANGO_SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')" >> .env```



Запустить контейнеры:
```cd infra```

```docker compose up --build```


Заполнить базу данных тестовыми данными:
```docker compose exec backend python manage.py migrate```

```docker compose exec backend python manage.py add_ingredients```

Если нужно добавить тестовых пользователей и рецепты:
```docker compose exec backend python manage.py loaddata data.json```


Перезапустить контейнеры:
```docker compose stop```

```docker compose up --build```


Сборка статики бекэнда для красивого отображения админ-панели:
```docker compose exec backend python manage.py collectstatic```

```docker compose exec backend cp -r /app/collected_static/. /backend_static/static/```

Создание суперпользователя:
```cd backend```

```python manage.py createsuperuser```


## Ссылки

[Документация API](http://localhost:8000/api/docs/)

[Админ-панель](http://localhost:8000/admin/)

[Главная страница](http://localhost:8000/recipes)