from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator
from django.db.models import Q

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(max_length=128)
    measurement_unit = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipe'
    )
    name = models.CharField(max_length=128)
    text = models.CharField(max_length=256)
    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,
    )
    ingredients = models.ManyToManyField(Ingredient, through="RecipeIngredient")
    cooking_time = models.PositiveIntegerField()


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe')
    name = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='ingredient')
    amount = models.IntegerField()

    class Meta:
        unique_together = ('recipe', 'name')


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower'
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following'
    )

    class Meta:
        unique_together = ('user', 'following')
        constraints = [
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='prevent_self_following'
            )
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='member'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorite'
    )

    class Meta:
        unique_together = ('user', 'recipe')


class ShoppingList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='list_owner')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe_in_list')

    class Meta:
        unique_together = ('user', 'recipe')

    '''def __str__(self):
        return f"{self.user.username} — {self.recipe.name}"    # Один рецепт один раз в списке
'''