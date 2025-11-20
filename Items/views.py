import stripe
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from .models import Item, Order


# Create your views here.

def get_item(request, id : int):
    """ Функция отображения страницы с информацией о товаре.
    Args:
        request: HTTP запрос от браузера
        id: идентификатор товара
    Returns:
        HTML страница с информацией о товаре """
    item = get_object_or_404(Item, id=id)
    publishable_key, _ = get_stripe_keys(item.currency)

    context = {
        'item': item,
        'stripe_publishable_key': publishable_key,
        'payment_method': 'session',
    }
    return render(request, 'Items/item_detail.html', context)

def buy_item(request, id : int):
    """ Функция создания сессии для оплаты
    Args:
        request: HTTP запрос
        id: идентификатор товара
    Returns:
        JSON с session_id для редиректа на Stripe Checkout """
    item = get_object_or_404(Item, id=id)
    if item.currency == 'rub':
        unit_amount = int(item.price * 100)
    else:
        unit_amount = int(item.price * 100)
    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': item.currency,
                    'product_data': {
                        'name': item.name,
                        'description': item.description,
                    },
                    'unit_amount': unit_amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri('/success/'),
            cancel_url=request.build_absolute_uri('/cancel/'),
        )

        return JsonResponse({'id': session.id})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def success(request) -> render:
    """ Страница успешной оплаты
    Args:
        request: HTTP запрос
    Returns:
        HTML страница с сообщением об успехе
    """
    return render(request, 'Items/success.html')

def get_stripe_keys(currency: str) -> tuple:
    """ Возвращает ключи Stripe
    """
    return settings.STRIPE_PUBLISHABLE_KEY, settings.STRIPE_SECRET_KEY

def create_payment_intent_item(request, id: int) -> JsonResponse:
    """ Создает Payment Intent для отдельного товара
    Args:
        request: HTTP запрос
        id: идентификатор товара
    Returns:
        JSON с client_secret для подтверждения платежа
    """
    item = get_object_or_404(Item, id=id)
    _, secret_key = get_stripe_keys(item.currency)

    if not secret_key:
        return JsonResponse({'error': 'Stripe secret key not configured'}, status=500)
    stripe.api_key = secret_key
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(item.price * 100),
            currency=item.currency,
            metadata={
                'item_id': item.id,
                'product_name': item.name
            }
        )
        return JsonResponse({
            'clientSecret': intent.client_secret,
            'publishableKey': settings.STRIPE_PUBLISHABLE_KEYS.get(item.currency)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def create_payment_intent_order(request, order_id: int) -> JsonResponse:
    """ Создает Payment Intent для заказа с несколькими товарами
    Args:
        request: HTTP запрос
        order_id: идентификатор заказа
    Returns:
        JSON с client_secret для подтверждения платежа
    """
    order = get_object_or_404(Order, id=order_id)
    currency = order.get_currency()
    _, secret_key = get_stripe_keys(currency)
    if not secret_key:
        return JsonResponse({'error': 'Stripe secret key not configured'}, status=500)
    stripe.api_key = secret_key
    try:
        total_amount = order.calculate_total()
        intent_params = {
            'amount': int(total_amount * 100),
            'currency': currency,
            'metadata': {
                'order_id': order.id,
                'type': 'order'
            }
        }
        if hasattr(order, 'discount') and order.discount.coupon_id:
            intent_params['discounts'] = [{
                'coupon': order.discount.coupon_id
            }]
        if hasattr(order, 'tax'):
            intent_params['automatic_tax'] = {'enabled': True}
        intent = stripe.PaymentIntent.create(**intent_params)
        return JsonResponse({
            'clientSecret': intent.client_secret,
            'publishableKey': settings.STRIPE_PUBLISHABLE_KEYS.get(currency)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def get_order(request, order_id: int) -> render:
    """ Страница заказа с кнопкой оплаты через Payment Intent
    Args:
        request: HTTP запрос
        order_id: идентификатор заказа
    Returns:
        HTML страница с информацией о заказе
    """
    order = get_object_or_404(Order, id=order_id)
    publishable_key, _ = get_stripe_keys(order.get_currency())
    order_items = order.orderitem_set.select_related('item').all()
    context = {
        'order': order,
        'order_items': order_items,
        'stripe_publishable_key': publishable_key,
        'payment_method': 'intent',
    }
    return render(request, 'Items/order_detail.html', context)


def buy_order(request, order_id: int) -> JsonResponse:
    """ Функция создания сессии для оплаты заказа
    Args:
        request: HTTP запрос
        order_id: идентификатор заказа
    Returns:
        JSON с session_id для редиректа на Stripe Checkout
    """
    order = get_object_or_404(Order, id=order_id)
    currency_groups = order.get_orders_by_currency()
    if len(currency_groups) > 1:
        return JsonResponse(
            {'error': 'Заказ содержит товары в разных валютах. Создайте отдельные заказы для каждой валюты.'},
            status=400)
    currency = list(currency_groups.keys())[0]
    order_items = currency_groups[currency]
    _, secret_key = get_stripe_keys(currency)
    stripe.api_key = secret_key

    try:
        line_items = []
        for order_item in order_items:
            line_items.append({
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': order_item.item.name,
                        'description': f"Количество: {order_item.quantity}",
                    },
                    'unit_amount': int(order_item.item.price * 100),
                },
                'quantity': order_item.quantity,
            })

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri('/success/'),
            cancel_url=request.build_absolute_uri('/cancel/'),
        )

        return JsonResponse({'id': session.id})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)





