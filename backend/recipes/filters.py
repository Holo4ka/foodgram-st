from rest_framework.filters import SearchFilter
import django_filters
from .models import Recipe

class NameSearchFilter(SearchFilter):
    search_param = 'name'


class RecipeShoppingListFilter(django_filters.FilterSet):
    is_in_shopping_list = django_filters.BooleanFilter(method='filter_in_shopping_list')

    class Meta:
        model = Recipe
        fields = ('is_in_shopping_list',)

    def filter_in_shopping_list(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(author=user)  # in_shopping_lists__user
        return queryset
