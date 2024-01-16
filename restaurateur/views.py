from django import forms
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View

from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem
from restaurateur.helper_functions import get_location, calculate_distance


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


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = Order.objects.exclude(status="delivered").prefetch_related(
        "contents"
    ).with_total_price().ordered_by_status_and_id()
    menu_items = RestaurantMenuItem.objects.prefetch_related("product")

    restaurant_contents = {}
    for restaurant in menu_items.values_list("restaurant", flat=True).distinct():
        restaurant_contents[restaurant] = [
            menu_item.product.id for menu_item in menu_items.filter(restaurant=restaurant)
        ]
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

    serialized_orders = []
    for order in orders:
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
            "available_restaurants": [{
                "restaurant": restaurant,
                "distance": calculate_distance(get_location(restaurant.address), order_location)
            } for restaurant in order.available_restaurants.all()],
            "cooked_by": order.cooked_by
        })

    return render(request, template_name='order_items.html', context={
        "order_items": serialized_orders
    })
