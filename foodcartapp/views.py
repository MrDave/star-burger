from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
import phonenumbers

from .models import Product, Order


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def check_for_invalid_attributes(order_payload):
    payload_attributes = ["products", "firstname", "lastname", "phonenumber", "address"]
    missing_attributes = []
    empty_attributes = []
    for attribute in payload_attributes:
        try:
            order_payload[attribute]
        except KeyError:
            missing_attributes.append(attribute)
    if missing_attributes:
        content = {", ".join(attribute for attribute in missing_attributes): "required field(s)"}
        return True, content

    for attribute in payload_attributes:
        if not order_payload[attribute]:
            empty_attributes.append(attribute)
    if empty_attributes:
        content = {", ".join(attribute for attribute in empty_attributes): "field(s) must not be empty"}
        return True, content

    if not isinstance(order_payload["products"], list):
        content = {"products": "must be a list"}
        return True, content

    non_str_attributes = []
    for attribute in ["firstname", "lastname", "phonenumber", "address"]:
        if not isinstance(order_payload[attribute], str):
            non_str_attributes.append(attribute)
    if non_str_attributes:
        content = {", ".join(attribute for attribute in non_str_attributes): "not a valid sting"}
        return True, content

    if not phonenumbers.is_valid_number(phonenumbers.parse(order_payload["phonenumber"])):
        content = {"phonenumber": "is not a valid phone number"}
        return True, content

    for item in order_payload["products"]:
        if not item:
            content = {"products": "cannot contain an empty object"}
            return True, content
        if not isinstance(item["product"], int) or not Product.objects.filter(id=item["product"]).exists():
            content = {"products": f"invalid primary key {item['product']}"}
            return True, content
        if not isinstance(item["quantity"], int) or item["quantity"] < 1:
            content = {"products": f"invalid quantity for product {item['product']}"}
            return True, content

    return False, None


@api_view(["POST"])
def register_order(request):
    try:
        payload = request.data
    except ValueError as error:
        return JsonResponse({
            "Error": error
        })

    is_invalid, content = check_for_invalid_attributes(payload)
    if is_invalid:
        return Response(content, status=status.HTTP_400_BAD_REQUEST)

    order = Order.objects.create(
        first_name=payload["firstname"],
        last_name=payload["lastname"],
        phone=payload["phonenumber"],
        address=payload["address"]
    )

    for item in payload["products"]:
        order.contents.create(
            item=Product.objects.get(id=item["product"]),
            amount=item["quantity"]
        )
    return JsonResponse({})
