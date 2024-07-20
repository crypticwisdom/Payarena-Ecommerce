from rest_framework import serializers
from .models import *


class CitySerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)

    class Meta:
        model = City
        exclude = []


class StateSerializer(serializers.ModelSerializer):
    cities = serializers.SerializerMethodField()

    def get_cities(self, obj):
        cities = None
        if City.objects.filter(state=obj).exists():
            cities = CitySerializer(City.objects.filter(state=obj), many=True,
                                    context={'request': self.context.get('request')}).data
        return cities

    class Meta:
        model = State
        exclude = []


class CountrySerializer(serializers.ModelSerializer):
    states = serializers.SerializerMethodField()

    def get_states(self, obj):
        state = None
        if State.objects.filter(country=obj).exists():
            state = StateSerializer(State.objects.filter(country=obj), many=True).data
        return state

    class Meta:
        model = Country
        exclude = []





