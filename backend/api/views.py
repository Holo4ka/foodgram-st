from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http import FileResponse, JsonResponse
from djoser.views import UserViewSet
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
import os
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
        base_url = request.build_absolute_uri('/')
        return JsonResponse(
            {'short-link': f'{base_url}s/{pk}'},
            status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='favorite')
    def add_to_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response({'detail': 'Рецепт уже в избранном.'},
                            status=status.HTTP_400_BAD_REQUEST)

        Favorite.objects.create(user=user, recipe=recipe)
        serializer = ShortRecipeSerializer(recipe,
                                           context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @add_to_favorite.mapping.delete
    def delete_from_favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)

        try:
            favorite = Favorite.objects.get(user=user, recipe=recipe)
        except Favorite.DoesNotExist:
            raise NotFound('Рецепт не найден в избранном.')

        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='shopping_cart')
    def add_to_shopping_list(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        # Проверка на дубликат
        if ShoppingList.objects.filter(user=user, recipe=recipe).exists():
            return Response({'detail': 'Рецепт уже в списке покупок.'},
                            status=status.HTTP_400_BAD_REQUEST)

        ShoppingList.objects.create(user=user, recipe=recipe)

        serializer = ShortRecipeSerializer(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @add_to_shopping_list.mapping.delete
    def delete_from_shopping_list(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        shopping_item = get_object_or_404(ShoppingList, user=user,
                                          recipe=recipe)

        shopping_item.delete()
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
                recipe=recipe).order_by('name')
            recipes.add(recipe)
            for ingredient in recipe_ingredients.all():
                if ingredient.name not in ingredients:
                    ingredients[ingredient.name] = {
                        'amount': ingredient.amount,
                        'measurement_unit': ingredient.measurement_unit
                    }
                else:
                    ingredients[ingredient.name]['amount'] += ingredient.amount
        filename = 'shopping_list.txt'
        file_path = os.path.join('media', filename)
        to_str = []
        for key in ingredients.keys():
            to_str.append(f"{key.name.capitalize()} - {ingredients[key]['amount']} {ingredients[ingredient.name]['measurement_unit']}")
        recipes = [recipe.name.capitalize() for recipe in recipes]
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f'Список покупок от {str(datetime.datetime.now().replace(second=0, microsecond=0))[:-3]}:\n\n')
            f.write('\n'.join(['Продукты:\n',
                '\n'.join(to_str), '\n',
                'Для рецептов:\n',
                '\n'.join(recipes),
            ]))
        response = FileResponse(open(file_path, 'rb'), content_type='text/plain')
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

        if Follow.objects.filter(user=user, following=user_to_follow).exists():
            return Response(
                {'error': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST)

        Follow.objects.create(user=user, following=user_to_follow)
        serializer = FollowUserSerializer(user_to_follow,
                                          context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @follow.mapping.delete
    def unfollow(self, request, id=None):
        user = request.user
        user_to_unfollow = get_object_or_404(User, id=id)
        following_instance = get_object_or_404(
            Follow, user=user,
            following=user_to_unfollow)
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
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)
