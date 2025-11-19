# items/stripe_utils.py
import stripe
from django.conf import settings
from .models import Discount, Tax


def get_stripe_api_key(currency):
    """ Возвращает секретный ключ Stripe для валюты """
    return settings.STRIPE_SECRET_KEYS.get(currency) or settings.STRIPE_SECRET_KEY


def create_stripe_coupon(discount):
    """ Создает купон в Stripe для скидки """
    currency = discount.order.get_currency()
    stripe.api_key = get_stripe_api_key(currency)

    try:
        coupon = stripe.Coupon.create(
            percent_off=discount.percent_off,
            duration='once',
            name=f"Discount {discount.percent_off}% for Order #{discount.order.id}"
        )
        discount.coupon_id = coupon.id
        discount.save()
        return coupon
    except Exception as e:
        print(f"Error creating Stripe coupon: {e}")
        return None


def create_stripe_tax_rate(tax):
    """ Создает налоговую ставку в Stripe """
    currency = tax.order.get_currency()
    stripe.api_key = get_stripe_api_key(currency)
    try:
        tax_rate = stripe.TaxRate.create(
            display_name=f"Tax {tax.tax_rate}%",
            percentage=tax.tax_rate,
            inclusive=False,
            country='RU',
        )
        tax.tax_id = tax_rate.id
        tax.save()
        return tax_rate
    except Exception as e:
        print(f"Error creating Stripe tax rate: {e}")
        return None


def setup_stripe_objects_for_order(order):
    """ Настраивает все необходимые Stripe объекты для заказа """
    if hasattr(order, 'discount') and not order.discount.coupon_id:
        create_stripe_coupon(order.discount)
    if hasattr(order, 'tax') and not order.tax.tax_id:
        create_stripe_tax_rate(order.tax)