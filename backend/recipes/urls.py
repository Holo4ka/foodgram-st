from rest_framework import routers
from django.urls import path, include
from .views import IngredientViewSet, RecipeViewSet, FollowViewSet

router = routers.DefaultRouter()
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
    # path('recipes/<int:recipe_id>/shopping_cart/', ),
    path('users/subscriptions/', FollowViewSet.as_view(
        {'get': 'list'}
    )),
    path('users/<int:user_id>/subscribe/', FollowViewSet.as_view(
        {'post': 'create', 'delete': 'destroy'}
    )),
]