from rest_framework import serializers
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from django.contrib.auth import get_user_model
from recipes.models import (Ingredient, Recipe, Follow,
                            RecipeIngredient, ShoppingList, Favorite)

User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = fields


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit', read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class IngredientWriteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    # password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'avatar', 'is_subscribed')
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        author = self.context['request'].user
        if not author:
            return False
        queryset = Follow.objects.filter(
            user=author.id
        ).filter(following=obj.id)
        if queryset:
            return True
        return False


class UserRegistrationSerializer(UserSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar', None)
        instance.save()
        return instance


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False)
    author = CustomUserSerializer(
        read_only=True)
    ingredients = IngredientWriteSerializer(many=True, write_only=True)
    # ingredients = RecipeIngredientSerializer(required=False, many=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'ingredients', 'image',
                  'name', 'text', 'cooking_time', 'is_in_shopping_cart',
                  'is_favorited')

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return ShoppingList.objects.filter(user=user, recipe=obj).exists()

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def create_recipe_ingredients_list(self, recipe, ingredients):
        recipe_ingredients = [RecipeIngredient(
            recipe=recipe,
            ingredient=Ingredient.objects.get(id=ingredient['id']),
            amount=ingredient['amount']
        ) for ingredient in ingredients]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = super().create({**validated_data})
        self.create_recipe_ingredients_list(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        old_ingrs = instance.ingredients_in_recipes.all()
        old_ingrs.delete()
        self.create_recipe_ingredients_list(instance, ingredients)
        return instance

    def to_representation(self, instance):
        """Переопределяем метод для корректного отображения ингредиентов."""
        representation = super().to_representation(instance)
        ingredients = RecipeIngredient.objects.filter(recipe=instance)
        representation['ingredients'] = RecipeIngredientSerializer(
            ingredients, many=True).data
        return representation


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class FollowUserSerializer(CustomUserSerializer):
    recipes_count = serializers.IntegerField(source='recipe.count',
                                             read_only=True)
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'avatar', 'is_subscribed', 'recipes_count', 'recipes')
        read_only_fields = fields

    def get_recipes(self, obj):
        # recipes = obj.recipe.filter(author=obj).all()
        recipes = obj.recipes.all()

        request = self.context['request']
        recipes_limit = request.query_params.get('recipes_limit') if request else None
        if recipes_limit is not None and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]
        return ShortRecipeSerializer(
            recipes,
            many=True,
            context={'request': self.context['request']}).data
