from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from djoser.views import UserViewSet
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.decorators import api_view, authentication_classes, \
    permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authentication import TokenAuthentication

from .pagination import PageLimitPagination
from .models import Recipe, Ingredient, Follow, User, \
    Favorite, ShoppingList, RecipeIngredient
from .serializers import RecipeSerializer, IngredientSerializer, \
    FollowSerializer, CustomUserSerializer, FollowUserSerializer, \
        FavoriteSerizlier, ShortRecipeSerializer, ShoppingListSerializer, \
            AvatarSerializer
from .filters import NameSearchFilter, RecipeShoppingListFilter


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
    
    def perform_update(self, serializer):
        serializer.save(author=self.request.user)


class FavoriteRecipeViewSet(viewsets.ViewSet):
    def get_queryset(self):
        return Favorite.objects.filter(member=self.request.user)
    
    def create(self, request, recipe_id=None):
        all_recipes = Recipe.objects.all()
        recipe_to_follow = get_object_or_404(all_recipes, pk=recipe_id)
        author = self.request.user
        serializer = FavoriteSerizlier(data=request.data,
                                        context={'request': request})
        if serializer.is_valid() and request.user.is_authenticated:
            serializer.save(user=author, recipe=recipe_to_follow)

            output = ShortRecipeSerializer(recipe_to_follow,
                                           data=request.data,
                                           context={'request': request}
                                           )
            if output.is_valid():
                return Response(output.data, status=status.HTTP_201_CREATED)
            return Response(output.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, recipe_id=None):
        recipe_to_unfollow = Recipe.objects.get(id=recipe_id)
        author = self.request.user
        favorite_instance = Favorite.objects.get(
            user=author, recipe=recipe_to_unfollow
            )
        serializer = FavoriteSerizlier(favorite_instance,
                                       data=request.data,
                                       context={'request': request})
        if serializer.instance.user != author:
            raise PermissionDenied(
                'Нельзя удалять рецепт из избранного чужого пользователя!'
                )
        favorite_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageLimitPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('following__username',)

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)

    def create(self, request, user_id=None):
        try:
            user_to_follow = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if self.request.user == user_to_follow:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = FollowSerializer(data=request.data,
                                      context={'request': request})
        if serializer.is_valid() and request.user.is_authenticated:
            serializer.save(user=self.request.user, following=user_to_follow)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, user_id=None):
        try:
            user_to_unfollow = User.objects.get(id=user_id)
            following_instance = Follow.objects.get(
                user=request.user, following=user_to_unfollow
                )
        except Follow.DoesNotExist:
            raise(NotFound())
        serializer = FollowSerializer(following_instance,
                                      data=request.data, partial=True)
        if serializer.instance.user != request.user:
            raise PermissionDenied('Удаление чужой подписки запрещено!')
        following_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request):
        followings = Follow.objects.filter(user=self.request.user)
        following_user_ids = followings.values_list(
            'following__id', flat=True
            )
        queryset = User.objects.filter(id__in=following_user_ids)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = FollowUserSerializer(
                page,
                many=True,
                context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = FollowUserSerializer(
            queryset,
            many=True,
            context={'request': request})
        return Response(serializer.data)


class ShoppingListViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return ShoppingList.objects.filter(user=self.request.user)
    
    def create(self, request, recipe_id=None):
        all_recipes = Recipe.objects.all()
        recipe_to_add = get_object_or_404(all_recipes, pk=recipe_id)
        author = self.request.user
        serializer = ShoppingListSerializer(data=request.data,
                                            context={'request': request})
        if serializer.is_valid() and request.user.is_authenticated:
            serializer.save(user=author, recipe=recipe_to_add)

            output = ShortRecipeSerializer(recipe_to_add,
                                           data=request.data,
                                           context={'request': request}
                                           )
            if output.is_valid():
                return Response(output.data, status=status.HTTP_201_CREATED)
            return Response(output.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, recipe_id=None):
        all_recipes = Recipe.objects.all()
        recipe_to_delete = get_object_or_404(all_recipes, pk=recipe_id)
        author = self.request.user
        shopping_list_instance = ShoppingList.objects.get(
            user=author, recipe=recipe_to_delete
            )
        serializer = ShoppingListSerializer(shopping_list_instance,
                                            data=request.data,
                                            context={'request': request})
        if serializer.instance.user != author:
            raise PermissionDenied('Нельзя удалять чужой рецепт из списка покупок!')
        shopping_list_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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

    def list(self, request):
        queryset = self.get_queryset()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CustomUserSerializer(
                page,
                many=True,
                context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = CustomUserSerializer(
            queryset,
            many=True,
            context={'request': request})
        return Response(serializer.data)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def download_shopping_list(request):
    shopping_list = ShoppingList.objects.filter(user=request.user)
    ingredients = {}
    for item in shopping_list:
        recipe = item.recipe
        recipe_ingredients = RecipeIngredient.objects.filter(recipe=recipe)
        for ingredient in recipe_ingredients.all():
            if ingredient.name not in ingredients:
                ingredients[ingredient.name] = {
                    'amount': ingredient.amount,
                    'measurement_unit': ingredient.measurement_unit
                }
            else:
                ingredients[ingredient.name]['amount'] += ingredient.amount

    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
    response.write('Список покупок:\n\n')
    for name, data in ingredients.items():
        response.write(f'{name}: {data["amount"]} {data["measurement_unit"]}\n')

    return response


@api_view(['GET'])
def get_short_url(request, recipe_id=None):
    recipe = Recipe.objects.get(id=recipe_id)
    short_url = recipe.short_url
    return JsonResponse(
        {'short-link': f'localhost:8000/s/{short_url}'},
        status=status.HTTP_200_OK
        )


def extract_from_short_url(request, link=None):
    recipe = Recipe.objects.get(short_url=link)
    print(recipe)
    return redirect(f'/recipes/{recipe.id}/')
