# from rest_framework import serializers
# from .models import Item
#
# class ItemSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Item
#         fields = ['id', 'title', 'price']
from rest_framework import serializers
from .models import Item

class ItemSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = ['id', 'title', 'price']

    def get_price(self, obj):
        return float(obj.price)
