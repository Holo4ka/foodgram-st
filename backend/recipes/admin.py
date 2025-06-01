from django.contrib import admin
from .models import Recipe, Ingredient, \
    RecipeIngredient, Follow, Favorite, \
    ShoppingList, User

class UserAdmin(admin.ModelAdmin):
    search_fields = ('email', 'username')


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'name',
        'favorite_count',
    )
    search_fields = ('author', 'name')

    def favorite_count(self, obj):
        count = Favorite.objects.filter(recipe=obj).count()
        return count


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'measurement_unit',
        'name'
    )
    search_fields = ('name',)


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(RecipeIngredient)
admin.site.register(Follow)
admin.site.register(Favorite)
admin.site.register(ShoppingList)
admin.site.register(User, UserAdmin)
