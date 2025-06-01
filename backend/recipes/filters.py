from rest_framework.filters import SearchFilter
import django_filters
from .models import Recipe

class NameSearchFilter(SearchFilter):
    search_param = 'name'


class RecipeShoppingListFilter(django_filters.FilterSet):
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_in_shopping_cart'
        )
    is_favorited = django_filters.NumberFilter(method='filter_is_favorited')
    author = django_filters.NumberFilter(field_name='author__id')

    class Meta:
        model = Recipe
        fields = ('is_in_shopping_cart', 'is_favorited')

    def filter_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous or not value:
            return queryset
        return queryset.filter(recipe_in_list__user=user)

    
    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous or not value:
            return queryset
        return queryset.filter(favorite__user=user)
