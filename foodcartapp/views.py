from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response

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


@api_view(["POST"])
def register_order(request):
    try:
        payload = request.data
    except ValueError as error:
        return JsonResponse({
            "Error": error
        })

    try:
        payload["products"]
    except KeyError:
        content = {"products": "required field"}
        return Response(content, status=status.HTTP_400_BAD_REQUEST)
    if not payload["products"]:
        content = {"products": "must not be empty"}
        return Response(content, status=status.HTTP_400_BAD_REQUEST)
    elif not isinstance(payload["products"], list):
        content = {"products": "must be a list"}
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
