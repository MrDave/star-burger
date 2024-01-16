import requests
from django import forms
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.db.models import F, Value
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.conf import settings
from geopy import distance
from django.utils import timezone

from coordinatesapp.models import Location
from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem

from datetime import datetime


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def get_location(address):

    location, created = Location.objects.get_or_create(
        address=address,
        defaults={
            "last_fetched": timezone.now()
        }
    )
    if created:
        coords = fetch_coordinates(settings.YANDEX_API_KEY, location.address)
        if coords:
            location.lon, location.lat = coords
            location.save()
    return location


# def calculate_distance(location_1, location_2):
#     try:
#         order_coords = fetch_coordinates(settings.YANDEX_API_KEY, order_address)
#         restaurant_coords = fetch_coordinates(settings.YANDEX_API_KEY, restaurant_address)
#     except (requests.HTTPError,):
#         return "Ошибка определения координат"
#     if not order_coords:
#         return "Ошибка определения координат"
#     distance_to_restaurant = distance.distance(restaurant_coords, order_coords)
#     return distance_to_restaurant.km

def calculate_distance(location_1, location_2):
    coordinates_1 = location_1.lat, location_1.lon
    coordinates_2 = location_2.lat, location_2.lon
    if None not in coordinates_1 and None not in coordinates_2:
        return str(round(distance.distance(coordinates_1, coordinates_2).km, 2)) + " км"
    else:
        return "Ошибка определения координат"


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    view_start_time = datetime.now()
    print(f"{datetime.now()} - Start view function")
    orders = Order.objects.exclude(status="delivered").prefetch_related(
        "contents"
    ).with_total_price().ordered_by_status_and_id()
    menu_items = RestaurantMenuItem.objects.prefetch_related("product")

    print(f"{datetime.now()} - Beginning filling restaurant contents")
    restaurant_contents = {}
    for restaurant in menu_items.values_list("restaurant", flat=True).distinct():
        restaurant_contents[restaurant] = [
            menu_item.product.id for menu_item in menu_items.filter(restaurant=restaurant)
        ]
    print(f"{datetime.now()} - Beginning for order in orders cycle")
    for order in orders:
        available_restaurants = []
        for restaurant in restaurant_contents:
            order_availability = [
                product in restaurant_contents[restaurant]
                for product in order.contents.values_list("product", flat=True)
            ]
            if False not in order_availability:
                available_restaurants.append(restaurant)
        order.available_restaurants.set(available_restaurants)

    print(f"{datetime.now()} - Beginning serializing orders")
    serialized_orders = []
    for order in orders:
        print(f"{datetime.now()}Start order id{order.id}\nAddress: {order.address}")
        start_time = datetime.now()

        order_location = get_location(order.address)

        serialized_orders.append({
            "id": order.id,
            "firstname": order.firstname,
            "lastname": order.lastname,
            "phonenumber": order.phonenumber,
            "address": order.address,
            "total_price": order.total_price,
            "edit_link": reverse("admin:foodcartapp_order_change", args=(order.id,)),
            "status": order.get_status_display(),
            "comments": order.comments,
            "payment_method": order.get_payment_method_display(),
            # "available_restaurants": order.available_restaurants.annotate(
            #     distance=Value(calculate_distance(order.address, F("address")))
            # ),
            "available_restaurants": [{
                "restaurant": restaurant,
                "distance": calculate_distance(get_location(restaurant.address), order_location)
            } for restaurant in order.available_restaurants.all()],
            # Попытка сделать запрос не через annotate, а отдельно. Annotate -- задокументированный код выше
            "cooked_by": order.cooked_by
        })
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"Order id{order.id} completed in {duration.seconds} seconds.")
    view_end_time = datetime.now()
    total_view_duration = view_end_time - view_start_time
    print(f"{datetime.now()} - all done!\nView rendered in {total_view_duration}")
    return render(request, template_name='order_items.html', context={
        "order_items": serialized_orders
    })
