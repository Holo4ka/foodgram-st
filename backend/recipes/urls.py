from rest_framework import routers
from django.urls import path, include
from .views import IngredientViewSet, RecipeViewSet, \
    FollowViewSet, CustomUserViewSet, \
        FavoriteRecipeViewSet, ShoppingListViewSet, AvatarViewSet

router = routers.DefaultRouter()
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('users/subscriptions/', FollowViewSet.as_view(
        {'get': 'list'}
    )),
    path('users/me/avatar/', AvatarViewSet.as_view({'put': 'update'})),
    path('', include(router.urls)),
    path('recipes/<int:recipe_id>/shopping_cart/', ShoppingListViewSet.as_view(
        {'post': 'create', 'delete': 'destroy'}
    )),
    path('recipes/<int:recipe_id>/favorite/', FavoriteRecipeViewSet.as_view(
        {'post': 'create', 'delete': 'destroy'}
    )),
    path('users/<int:user_id>/subscribe/', FollowViewSet.as_view(
        {'post': 'create', 'delete': 'destroy'}
    )),
]

'''path('users/', CustomUserViewSet.as_view(
        {'get': 'list'}
    )),'''