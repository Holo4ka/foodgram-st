from rest_framework.filters import SearchFilter
import django_filters
from recipes.models import Recipe

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
        # return queryset.filter(recipe_in_list__user=user)
        if value:
            if self.request.user.is_authenticated:
                return queryset.filter(list_recipes__user=self.request.user)
            # Не фильтровать по автору, если пользователь неавторизован
            return queryset
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        if value:
            if self.request.user.is_authenticated:
                return queryset.filter(favorites__user=self.request.user)
            # Не фильтровать по автору, если пользователь неавторизован
