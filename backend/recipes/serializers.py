from rest_framework import serializers, status
from django.core.files.base import ContentFile
import base64
from djoser.serializers import UserSerializer
import random

from .models import Ingredient, Recipe, Follow, User, \
    RecipeIngredient, ShoppingList, Favorite


CHARACTERS = 'ABCDEFGHJKLMNOPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz234567890'
URL_LENGTH = 6


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    measurement_unit = serializers.CharField(required=False)

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
    
    def get_id(self, obj):
        ingr = Ingredient.objects.get(name=obj.name)
        return ingr.id
        


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    password  = serializers.CharField(write_only=True, required=True)

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
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance

 # , default=serializers.CurrentUserDefault()
class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)
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
    
    def create_short_url(self):
        while True:
                short_url = ''.join(
                    random.choices(
                        CHARACTERS,  
                        k=URL_LENGTH
                    )
                )
                if not Recipe.objects.filter(
                    short_url=short_url
                ).exists():
                    break
        return short_url
    
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
    
    def create(self, validated_data):
        _ = validated_data.pop('ingredients')
        ingredients = self.initial_data.get('ingredients')
        short_url = self.create_short_url()
        recipe = Recipe.objects.create(**validated_data, short_url=short_url)
        for ingredient in ingredients:
            ingr_id = ingredient['id']
            ingr_unit = Ingredient.objects.get(id=ingr_id)
            RecipeIngredient.objects.create(
                recipe=recipe,
                name=ingr_unit,
                amount=ingredient['amount'],
                measurement_unit=ingr_unit.measurement_unit
                )
        return recipe

    def update(self, instance, validated_data):
        _ = validated_data.pop('ingredients')
        ingredients = self.initial_data.get('ingredients')
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
            )
        instance.image = validated_data.get('image', instance.image)
        instance.save()
        old_ingrs = RecipeIngredient.objects.filter(recipe=instance)
        old_ingrs.delete()
        for ingredient in ingredients:
            ingr_id = ingredient['id']
            ingr_unit = Ingredient.objects.get(id=ingr_id)
            RecipeIngredient.objects.create(
                recipe=instance,
                name=ingr_unit,
                amount=ingredient['amount'],
                measurement_unit=ingr_unit.measurement_unit
                )
        return instance

    def to_representation(self, instance):
        """Переопределяем метод для корректного отображения ингредиентов."""
        representation = super().to_representation(instance)
        ingredients = RecipeIngredient.objects.filter(recipe=instance)
        representation['ingredients'] = RecipeIngredientSerializer(ingredients, many=True).data
        return representation


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False)
    name = serializers.CharField(required=False)
    cooking_time = serializers.IntegerField(required=False)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingListSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(
        read_only=True, default=serializers.CurrentUserDefault())
    recipe = RecipeSerializer(read_only=True)

    class Meta:
        model = ShoppingList
        fields = ('id', 'recipe', 'owner')



class FavoriteSerizlier(serializers.ModelSerializer):
    user = serializers.StringRelatedField(
        read_only=True, default=serializers.CurrentUserDefault())
    recipe = RecipeSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = '__all__'


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(
        read_only=True, default=serializers.CurrentUserDefault())
    following = CustomUserSerializer(read_only=True)

    class Meta:
        fields = ('following', 'user')
        model = Follow

    def create(self, validated_data):
        try:
            instance = Follow.objects.create(**validated_data)
            return instance
        except Exception as e:
            print(f'Serializer: {e}')
            raise serializers.ValidationError()
    
    def validate(self, data):
        """Проверяем, что не подписываемся на самого себя"""
        if self.context['request'].user != data.get('following'):
            return data
        raise serializers.ValidationError("Нельзя подписаться на самого себя")


class FollowUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 
                  'avatar', 'is_subscribed', 'recipes_count', 'recipes')
    
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
    
    def get_recipes(self, obj):
        recipes = obj.recipe.filter(author=obj).all()[:3]
        return ShortRecipeSerializer(
            recipes,
            many=True,
            context={'request': self.context['request']}).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()
