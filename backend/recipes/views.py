from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from djoser.views import UserViewSet
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import NotFound, PermissionDenied

from .permissions import AuthorOrReadOnly
from .pagination import CustomLimitOffsetPagination
from .models import Recipe, Ingredient, Follow, User
from .serializers import RecipeSerializer, IngredientSerializer, FollowSerializer
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
    # permission_classes = (AuthorOrReadOnly,)
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeShoppingListFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class FollowViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('following__username',)

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)

    def create(self, request, user_id=None):
        print('Вход')
        # to_follow = self.request.data.get('following')
        try:
            user_to_follow = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if self.request.user == user_to_follow:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        print('Два')
        serializer = FollowSerializer(data=request.data,
                                      context={'request': request})
        if serializer.is_valid() and request.user.is_authenticated:
            print('Три')
            serializer.save(user=self.request.user, following=user_to_follow)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request):
        try:
            following = Follow.objects.get(user=request.user)
        except Follow.DoesNotExist:
            raise(NotFound())

        serializer = FollowSerializer(following,
                                       data=request.data, partial=True)
        if serializer.instance.author != request.user:
            raise PermissionDenied('Удаление чужой подписки запрещено!')
        following.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request):
        queryset = self.get_queryset()
        search_terms = request.query_params.get('search', None)
        if search_terms:
            # Пример фильтрации по полям title и description
            queryset = queryset.filter(
                Q(following__username__icontains=search_terms))
        serializer = FollowSerializer(queryset, many=True)
        return Response(serializer.data)


class CustomUserViewSet(UserViewSet):
    pagination_class = CustomLimitOffsetPagination
