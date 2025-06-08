from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http import FileResponse, JsonResponse
from djoser.views import UserViewSet
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
import datetime

from .pagination import PageLimitPagination
from recipes.models import (
    Recipe, Ingredient, Follow,
    Favorite, ShoppingList, RecipeIngredient)
from .serializers import (
    RecipeSerializer, IngredientSerializer, FollowUserSerializer,
    ShortRecipeSerializer, AvatarSerializer)
from .filters import NameSearchFilter, RecipeShoppingListFilter

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (NameSearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = PageLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeShoppingListFilter
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_url(self, request, pk=None):
        short_path = reverse('short-link', kwargs={'recipe_id': pk})
        full_url = request.build_absolute_uri(short_path)
        return JsonResponse({'short-link': full_url},
                            status=status.HTTP_200_OK)

    def add_to_favorite_or_shopping_list(self, request, pk, db_model):
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        favorite, created = db_model.objects.get_or_create(user=user,
                                                           recipe=recipe)
        if not created:
            return Response({'detail': f'Рецепт {recipe} уже в избранном.'},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = ShortRecipeSerializer(recipe,
                                           context={'request': request})
        return serializer

    def delete_from_favorite_or_shopping_list(self, request, pk, db_model):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        item = get_object_or_404(db_model, user=user,
                                 recipe=recipe)

        item.delete()

    @action(detail=True, methods=['post'], url_path='favorite')
    def add_to_favorite(self, request, pk=None):
        serializer = self.add_to_favorite_or_shopping_list(request, pk, Favorite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @add_to_favorite.mapping.delete
    def delete_from_favorite(self, request, pk=None):
        self.delete_from_favorite_or_shopping_list(request, pk, Favorite)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='shopping_cart')
    def add_to_shopping_list(self, request, pk=None):
        serializer = self.add_to_favorite_or_shopping_list(request, pk, ShoppingList)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @add_to_shopping_list.mapping.delete
    def delete_from_shopping_list(self, request, pk=None):
        self.delete_from_favorite_or_shopping_list(request, pk, ShoppingList)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart',
            permission_classes=[IsAuthenticated])
    def download_shopping_list(self, request):
        shopping_list = ShoppingList.objects.filter(user=request.user)
        ingredients = {}
        recipes = set()
        for item in shopping_list:
            recipe = item.recipe
            recipe_ingredients = RecipeIngredient.objects.filter(
                recipe=recipe)
            recipes.add(recipe)
            for ingredient in recipe_ingredients.all():
                if ingredient.ingredient not in ingredients:
                    ingredients[ingredient.ingredient.name] = {
                        'amount': ingredient.amount,
                        'measurement_unit': ingredient.ingredient.measurement_unit
                    }
                else:
                    ingredients[ingredient.name]['amount'] += ingredient.amount
        ingredients = dict(sorted(ingredients.items()))
        to_str = []
        for key in ingredients.keys():
            to_str.append(f"{key.capitalize()} - {ingredients[key]['amount']} {ingredients[ingredient.ingredient.name]['measurement_unit']}")
        recipes = [recipe.name for recipe in recipes]
        output = f'Список покупок от {str(datetime.datetime.now().replace(second=0, microsecond=0))[:-3]}:\n' + '\n'.join(
            ['Продукты:\n',
             '\n'.join(to_str), '\n',
             'Для рецептов:\n',
             '\n'.join(recipes),
             ])
        response = FileResponse(output, content_type='text/plain')
        # response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class AvatarViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AvatarSerializer
    queryset = User.objects.all()
    pagination_class = None

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class CustomUserViewSet(UserViewSet):
    pagination_class = PageLimitPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return User.objects.all()

    @action(detail=False, methods=['put'], url_path='me/avatar')
    def set_avatar(self, request):
        user = request.user
        serializer = AvatarSerializer(
            user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @set_avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='subscribe')
    def follow(self, request, id=None):
        user = request.user
        user_to_follow = get_object_or_404(User, id=id)

        if user == user_to_follow:
            return Response({'error': 'Нельзя подписаться на самого себя.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if user.followers.filter(following=user_to_follow).exists():
            return Response(
                {'error': f'Вы уже подписаны на пользователя {user_to_follow}.'},
                status=status.HTTP_400_BAD_REQUEST)

        Follow.objects.create(user=user, following=user_to_follow)
        serializer = FollowUserSerializer(user_to_follow,
                                          context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @follow.mapping.delete
    def unfollow(self, request, id=None):
        user = request.user
        # user_to_unfollow = get_object_or_404(User, id=id)
        following_instance = get_object_or_404(
            Follow, user=user,
            following__id=id)
        following_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def follow_list(self, request):
        followings = Follow.objects.filter(user=request.user)
        following_user_ids = followings.values_list('following__id', flat=True)
        queryset = User.objects.filter(id__in=following_user_ids)

        page = self.paginate_queryset(queryset)
        serializer = FollowUserSerializer(page or queryset, many=True,
                                          context={'request': request})
        return self.get_paginated_response(serializer.data)
