from django.db import models

class Item(models.Model):
    """
    Модель данных для товара.

    Поля:
    - id: id товара
    - title: наименование
    - price: стоимость
    """

    id = models.AutoField(primary_key=True, verbose_name='id')
    title = models.CharField(max_length=255, verbose_name='наименование')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='стоимость')

    def __str__(self):
        return self.title

