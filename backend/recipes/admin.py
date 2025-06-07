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
        return user

    def recipe_count(self, user):
        return Recipe.objects.filter(author=user).count()

    def followings_count(self, user):
        return Follow.objects.filter(following=user).count()

    def followers_count(self, user):
        return Follow.objects.filter(user=user).count()

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
        count = Favorite.objects.filter(recipe=recipe).count()
        return count

    def image(self, recipe):
        return mark_safe(f'<img src="{recipe.image.url}" width="40" />')

    def ingredients_display(self, recipe):
        ingredients_list = RecipeIngredient.objects.filter(
            recipe=recipe
        ).select_related('name')
        print(ingredients_list)
        if not ingredients_list:
            return "-"
        html = "<ul>"
        for ingr in ingredients_list:
            ingr_name = ingr.name.name
            html += f"<li><strong>{ingr_name}</strong> — {ingr.amount}</li>"
        html += "</ul>"
        return mark_safe(html)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'measurement_unit',
        'name',
        'recipes_count',
    )
    search_fields = ('name', 'measurement_unit', 'recipes_count')
    # Но зачем добавлять поиск по ед. изм.,
    # если в задании не указано?
    list_filter = ('measurement_unit',)

    def recipes_count(self, ingredient):
        count = RecipeIngredient.objects.filter(
            name=ingredient
        ).select_related('recipe').count()
        return count


admin.site.register(RecipeIngredient)
admin.site.register(Follow)
admin.site.register(Favorite)
admin.site.register(ShoppingList)
