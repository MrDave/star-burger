from django.db import models


class Location(models.Model):
    address = models.TextField(verbose_name="адрес", unique=True)
    lon = models.FloatField(verbose_name="долгота", null=True, blank=True)
    lat = models.FloatField(verbose_name="широта", null=True, blank=True)
    last_fetched = models.DateTimeField(verbose_name="дата проверки координат")

    def __str__(self):
        return self.address
