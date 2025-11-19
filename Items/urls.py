from django.urls import path
from . import views

urlpatterns = [
    path('item/<int:id>/', views.get_item, name='item_detail'),
    path('buy/<int:id>/', views.buy_item, name='buy_item'),
    path('success/', views.success, name='success'),
    path('item/<int:id>/pay/', views.create_payment_intent_item, name='pay_item'),
    path('order/<int:order_id>/', views.get_order, name='order_detail'),
    path('order/<int:order_id>/pay/', views.create_payment_intent_order, name='pay_order'),
    path('api/order/<int:order_id>/payment-intent/', views.create_payment_intent_order, name='api_payment_intent'),
]