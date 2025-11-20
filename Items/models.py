from django.db import models



# Create your models here.

class Item(models.Model):
    """ Модель товара для продажи через Stripe.
    Поля:
    - name: название товара
    - description: описание товара
    - price: цена товара
    - currency: валюта товара
    """

    CURRENCY_CHOICES = [
        ('usd', 'US Dollars'),
        ('eur', 'Euros'),
        ('rub', 'Russian Rubles'),
    ]
    name = models.CharField(max_length=100, verbose_name="Название товара")
    description = models.TextField(verbose_name="Описание товара")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='rub',
        verbose_name="Валюта"
    )

    def __str__(self):
        """ Строковое представление товара """
        return f"{self.name} - ({self.price})"

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

class Order(models.Model):
    """ Модель заказа, который объединяет несколько товаров.
     Поля:
     - items: товары в заказе
     - total_amount: общая сумма заказа
     - created_at: дата создания заказа
     """
    items = models.ManyToManyField(Item, through="OrderItem", verbose_name="Товары в заказе")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Общая сумма")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def calculate_total(self):
        """ Рассчитывает общую сумму заказа """
        total = 0
        for order_item in self.orderitem_set.all():
            total += order_item.item.price * order_item.quantity
        self.total_amount = total
        Order.objects.filter(id=self.id).update(total_amount=total)
        return total

    def get_orders_by_currency(self):
        """Разделяет заказ на подзаказы по валютам"""
        currency_groups = {}
        for order_item in self.orderitem_set.all():
            currency = order_item.item.currency
            if currency not in currency_groups:
                currency_groups[currency] = []
            currency_groups[currency].append(order_item)
        return currency_groups

    def save(self, *args, **kwargs):
        """Автоматически рассчитываем сумму при сохранении"""
        if self.pk:
            self.calculate_total()
        super().save(*args, **kwargs)

    def get_currency(self):
        """Возвращает валюту заказа (берет из первого товара)"""
        if self.orderitem_set.exists():
            return self.orderitem_set.first().item.currency
        return 'rub'

    def __str__(self):
        """ Строковое представление заказа """
        return f"Order #{self.id} - {self.total_amount} {self.get_currency()}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class OrderItem(models.Model):
    """ Промежуточная модель для связи заказа и товаров
         Поля:
     - order: связь с заказом
     - item: связь с товаром
     - quantity: количество товаров в заказе
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказах"

class Discount(models.Model):
    """ Модель скидки для заказов
         Поля:
     - order: заказ
     - percent_off: процент скидки заказа
     - coupon_id: Айди купона
    """
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='discount',
        verbose_name="Заказ"
    )
    percent_off = models.PositiveIntegerField(verbose_name="Процент скидки")
    coupon_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="ID купона в Stripe"
    )

    def save(self, *args, **kwargs):
        """ Сохранение скидки при заказе """
        super().save(*args, **kwargs)

    def __str__(self):
        """ Строковое представление скидки """
        return f"Скидка {self.percent_off}% для заказа #{self.order.id}"

    class Meta:
        verbose_name = "Скидка"
        verbose_name_plural = "Скидки"


class Tax(models.Model):
    """ Модель налога для заказов
         Поля:
     - items: заказ
     - total_amount: ставка налога при заказе
     - tax_id: Айди налога
     """
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='tax',
        verbose_name="Заказ"
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Ставка налога (%)"
    )
    tax_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="ID налога в Stripe"
    )

    def __str__(self):
        """ Строковое представление налога заказа """
        return f"Налог {self.tax_rate}% для заказа #{self.order.id}"

    def save(self, *args, **kwargs):
        """ Сохранение налоговой ставки """
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Налог"
        verbose_name_plural = "Налоги"
