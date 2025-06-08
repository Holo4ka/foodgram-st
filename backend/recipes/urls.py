from django.urls import path
from .views import extract_from_short_url

urlpatterns = [
    path('<int:recipe_id>/', extract_from_short_url, name='short-link')
]
