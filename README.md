## Проект FOODGRAM

# Запуск проекта:
Клонировать репозиторий:
```git clone https://github.com/Holo4ka/foodgram-st.git```
```cd foodgram-st```

Создать файл .env:
```cp .env.example .env```

Запустить контейнеры:
```cd infra```
```docker compose up --build```

Заполнить базу данных тестовыми данными (выполнять строго в этой последовательности):
```docker compose exec backend python manage.py migrate```
```docker compose exec backend python manage.py add_ingredients```
```docker compose exec backend python manage.py loaddata data.json```

Перезапустить контейнеры:
```docker compose stop```
```docker compose up --build```

Сборка статики бекэнда для красивого отображения админ-панели:
```docker compose exec backend python manage.py collectstatic```
```docker compose exec backend cp -r /app/collected_static/. /backend_static/static/```
