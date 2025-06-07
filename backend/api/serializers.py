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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    measurement_unit = serializers.CharField(required=False)
    amount = serializers.IntegerField(required=False)
    id = serializers.SerializerMethodField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'amount', 'measurement_unit',)
        read_only_fields = ('id', 'name', 'amount', 'measurement_unit',)

    def get_id(self, obj):
        ingr = Ingredient.objects.get(name=obj.name)
        return ingr.id


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'avatar', 'is_subscribed', 'password')

        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'password': {'write_only': True},
        }

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

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
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
    ingredients = RecipeIngredientSerializer(required=False, many=True)
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
        recipe_ingredients = []
        for ingredient in ingredients:
            ingr_id = ingredient['id']
            recipe_ingredients.append(RecipeIngredient(
                recipe=recipe,
                name=Ingredient.objects.get(id=ingr_id),
                amount=ingredient['amount'],
                measurement_unit=Ingredient.objects.get(
                    id=ingr_id).measurement_unit
            ))
        return recipe_ingredients

    def create(self, validated_data):
        _ = validated_data.pop('ingredients')
        ingredients = self.initial_data.get('ingredients')
        recipe = super().create({**validated_data})
        recipe_ingredients = self.create_recipe_ingredients_list(recipe,
                                                                 ingredients)
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return recipe

    def update(self, instance, validated_data):
        _ = validated_data.pop('ingredients')
        ingredients = self.initial_data.get('ingredients')
        instance = super().update({**validated_data})
        old_ingrs = instance.recipes.all()
        old_ingrs.delete()
        recipe_ingredients = self.create_recipe_ingredients_list(instance,
                                                                 ingredients)
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
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
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class FollowUserSerializer(CustomUserSerializer):
    recipes_count = serializers.IntegerField(source='recipe.count',
                                             read_only=True)
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'avatar', 'is_subscribed', 'recipes_count', 'recipes')
        read_only_fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'avatar', 'is_subscribed', 'recipes_count', 'recipes')

    def get_recipes(self, obj):
        recipes = obj.recipe.filter(author=obj).all()[:3]
        return ShortRecipeSerializer(
            recipes,
            many=True,
            context={'request': self.context['request']}).data
