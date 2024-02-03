from rest_framework import serializers

from foodcartapp.models import OrderContents, Order


class OrderContentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderContents
        fields = ["product", "quantity"]


class OrderSerializer(serializers.ModelSerializer):
    products = OrderContentsSerializer(many=True, allow_empty=False, write_only=True)

    class Meta:
        model = Order
        fields = ["id", "firstname", "lastname", "address", "phonenumber", "products"]
