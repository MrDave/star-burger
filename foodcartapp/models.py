from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum, F
from phonenumber_field.modelfields import PhoneNumberField


class OrderQuerySet(models.QuerySet):
    def with_total_price(self):
        return self.annotate(
            total_price=Sum(F("contents__quantity") * F("contents__product__price"), output_field=models.DecimalField())
        )


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class Order(models.Model):
    firstname = models.CharField(verbose_name="имя", max_length=100)
    lastname = models.CharField(verbose_name="фамилия", max_length=100)
    address = models.TextField(verbose_name="адрес доставки")
    phonenumber = PhoneNumberField(verbose_name="номер телефона")
    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = "заказ"
        verbose_name_plural = "заказы"
        indexes = [
            models.Index(fields=["lastname", "firstname"]),
            models.Index(fields=["phonenumber"])
        ]

    def __str__(self):
        return f"{self.lastname} - {self.phonenumber}"


class OrderContents(models.Model):
    order = models.ForeignKey(Order, verbose_name="заказ", on_delete=models.CASCADE, related_name="contents")
    product = models.ForeignKey(Product, verbose_name="товар", on_delete=models.CASCADE, related_name="+")
    quantity = models.IntegerField(verbose_name="количество", validators=[MinValueValidator(0)])
    cost = models.DecimalField(
        verbose_name="стоимость позиции",
        validators=[MinValueValidator(0)],
        decimal_places=2,
        max_digits=7,
    )

    def __str__(self):
        return f"{self.order} - {self.product}"

