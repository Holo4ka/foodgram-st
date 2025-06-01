from recipes.views import extract_from_short_url
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('s/<str:link>/', extract_from_short_url),
    path('admin/', admin.site.urls),
    path('api/', include('recipes.urls')),
    path('api/', include('djoser.urls')),  # Работа с пользователями
    path('api/auth/', include('djoser.urls.authtoken')),  # Работа с токенами
]
