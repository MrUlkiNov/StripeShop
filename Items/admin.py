from django.contrib import admin

from Items.models import Item


# Register your models here.

# items/admin.py
from django.contrib import admin
from .models import Item, Order, OrderItem, Discount, Tax


class OrderItemInline(admin.TabularInline):
    """Inline для отображения товаров в заказе"""
    model = OrderItem
    extra = 1


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'currency', 'description_short')
    list_filter = ('currency',)
    search_fields = ('name', 'description')

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description

    description_short.short_description = "Описание"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'total_amount', 'get_currency', 'created_at')
    inlines = [OrderItemInline]
    readonly_fields = ('total_amount',)

    def get_currency(self, obj):
        return obj.get_currency()

    get_currency.short_description = "Валюта"


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('order', 'percent_off', 'coupon_id')


@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ('order', 'tax_rate', 'tax_id')