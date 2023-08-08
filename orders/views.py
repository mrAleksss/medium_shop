from django.shortcuts import render, redirect
import datetime
from carts.models import CartItem
from .forms import OrderForm, PaymentForm
from .models import Order, Payment, OrderProduct
import json
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.http import JsonResponse


def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])
    # Store transaction details inside Payment model
    payment = Payment (
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid = order.order_total,
        status = body['status'],
    )
    payment.save()
    order.payment = payment
    order.is_ordered = True
    order.save()

    # Move the cart items to OrderProduct table
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.discounted_price.amount
        orderproduct.ordered = True
        orderproduct.save() 

        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variation.set(product_variation)
        orderproduct.save()

        # Reduce the quantity of the sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Clear cart
    CartItem.objects.filter(user=request.user).delete()

    # Send order recieved email to customer
    mail_subject = "Дякуємо за ваше замовлення!"
    message = render_to_string('orders/order_recieved_email.html', {
                'user': request.user,
                'order': order,
            })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send() 

    # Send order number and transaction id back to sendData method via JsonResponse
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }



    return JsonResponse(data)


def place_order(request, total=0, quantity=0):
    current_user = request.user
    # if cart_count is less or equal to 0 then redirect to shop 
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect("store")

    for cart_item in cart_items:
        total += cart_item.discounted_price*cart_item.quantity
        quantity += cart_item.quantity

    if request.method == 'POST':
        form = OrderForm(request.POST, prefix='order')
        payment_form = PaymentForm(request.POST, prefix='payment')
        if form.is_valid() and payment_form.is_valid():
            # Create Payment instance
            payment_method = payment_form.cleaned_data['payment_method']
            payment = Payment(payment_method=payment_method)
            # save the payment instance to get id
            payment.save()
            # Store all billing information inside the Order table
            # new option
            data = form.save(commit=False)
            data.email = current_user.email
            data.user = current_user
            data.order_total = total
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            # Associate the payment with order
            data.payment = payment
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
            }
            return render(request, "orders/payments.html", context)
        
        else:
            print(form.errors)
            print(payment_form.errors)
            context = {'form': OrderForm(request.POST)}
            return render(request, 'store/checkout.html', context)

    else:
        
        form = OrderForm(request.POST or None)
        payment_form = PaymentForm(request.POST or None)
        context = {
            'form': form,
            'payment_form': payment_form,
        }

        return render(request, 'store/checkout.html', context)
    

def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        total = 0
        for i in ordered_products:
            total += i.product_price * i.quantity

        payment = Payment.objects.get(payment_id=transID)

        context = {
            "order": order,
            "ordered_products": ordered_products,
            "order_number": order.order_number,
            "transID": payment.payment_id,
            "payment": payment,
            "total": total,
        }

        return render(request, 'orders/order_complete.html', context)
    
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
