from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinValueValidator


class RecipeUser(AbstractUser):
    avatar = models.ImageField(
        upload_to='media/users/',
        null=True,
        verbose_name='Аватар'
    )
    email = models.EmailField(
        unique=True,
        max_length=254,
        verbose_name='Адрес электронной почты'
    )
    username = models.CharField(
        max_length=150, unique=True,
        validators=[RegexValidator(regex=r'^[\w.@+-]+\Z')],
        verbose_name='Никнейм пользователя'
    )
    first_name = models.CharField(max_length=150,
                                  verbose_name='Имя пользователя')
    last_name = models.CharField(max_length=150,
                                 verbose_name='Фамилия пользователя')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return f'{self.username} ({self.first_name} {self.last_name})'


class Ingredient(models.Model):
    name = models.CharField(max_length=128, verbose_name='Ингредиент')
    measurement_unit = models.CharField(max_length=64,
                                        verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_measurement_unit')
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recipes',
        verbose_name='Автор рецепта'
    )
    name = models.CharField(max_length=256, verbose_name='Название')
    text = models.CharField(verbose_name='Описание действий')
    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,
        verbose_name='Изображение'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Время приготовления')

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients_in_recipes',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Количество ингредиента',
    )
    '''measurement_unit = models.CharField(
        max_length=64,
        null=True,
        verbose_name='Единица измерения ингредиента'
    )'''

    def __str__(self):
        return f'{self.recipe} - {self.ingredient}'

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient')
        ]


class Follow(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Кто подписан'
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='followings',
        verbose_name='На кого подписан'
    )

    def __str__(self):
        return f'Подписка {self.user} на {self.following}'

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='prevent_self_following'
            ),
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_user_following'),
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='favorite_recipes',
        verbose_name='Кто добавил'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorites',
        verbose_name='Рецепт'
    )

    def __str__(self):
        return f'Рецепт {self.recipe} в избранном пользователя {self.user}'

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_user_recipe')
        ]



class ShoppingList(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Владелец списка',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепты в списке',
    )

    def __str__(self):
        return f'Рецепт {self.recipe} в списке покупок пользователя {self.user}'

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_list_user_recipe')
        ]
