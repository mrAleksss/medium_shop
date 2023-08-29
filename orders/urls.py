from django.urls import path
from . import views


urlpatterns = [
    path("place_order/", views.place_order, name="place_order" ),
    path("my_payments/", views.payments, name="payments"),
    # path("generate_pdf/", views.generate_pdf, name="generate_pdf"),
    # path("order_complete/", views.order_complete, name="order_complete"),
]