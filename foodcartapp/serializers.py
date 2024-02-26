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

    def create(self, validated_data):
        order = Order.objects.create(
            firstname=validated_data["firstname"],
            lastname=validated_data["lastname"],
            phonenumber=validated_data["phonenumber"],
            address=validated_data["address"],
        )
        order_contents_fields = validated_data["products"]
        products = [field["product"] for field in order_contents_fields]
        prices = {product.id: product.price for product in products}
        order_contents = [OrderContents(
            order=order,
            cost=prices[fields["product"].id],
            **fields
        ) for fields in order_contents_fields]
        OrderContents.objects.bulk_create(order_contents)
        return order
