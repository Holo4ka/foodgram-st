from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from .models import (Recipe, Ingredient,
                     RecipeIngredient, Follow, Favorite,
                     ShoppingList)

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'id',
        'username',
        'full_name',
        'email',
        'avatar',
        'recipe_count',
        'followings_count',
        'followers_count',
    )
    search_fields = ('email', 'username')

    def full_name(self, user):
        return f'{user.last_name} {user.first_name}'

    def recipe_count(self, user):
        return user.recipes.count()

    def followings_count(self, user):
        return user.followings.count()

    def followers_count(self, user):
        return user.followers.count()

    def avatar(self, user):
        if user.avatar:
            return mark_safe(f'<img src="{user.avatar.url}" width="40" />')
        return "-"


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'name',
        'cooking_time',
        'favorite_count',
        'ingredients_display',
        'image',
    )
    search_fields = ('author', 'name')
    list_filter = ('author',)

    def favorite_count(self, recipe):
        count = recipe.favorites.count()
        return count

    def image(self, recipe):
        return mark_safe(f'<img src="{recipe.image.url}" width="40" />')

    def ingredients_display(self, recipe):
        ingredients_list = RecipeIngredient.objects.filter(
            recipe=recipe
        ).select_related('ingredient')
        html = ''
        '''for ingr in ingredients_list:
            html += f"<br><strong>{ingr.ingredient.name}</strong> — {ingr.amount} {ingr.ingredient.measurement_unit}</br>"
        html += "</br>"'''
        html = '</br>'.join(f'<strong>{ingr.ingredient.name}</strong> — {ingr.amount} {ingr.ingredient.measurement_unit}' for ingr in recipe.ingredients_in_recipes)
        return mark_safe(html)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'measurement_unit',
        'name',
        'recipes_count',
    )
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)


admin.site.register(RecipeIngredient)
admin.site.register(Follow)
admin.site.register(Favorite)
admin.site.register(ShoppingList)
