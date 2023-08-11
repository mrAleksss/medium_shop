from django.shortcuts import render, redirect
import datetime
from carts.models import CartItem
from .forms import OrderForm
from .models import Order, Payment, OrderProduct
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string



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
    print(total)
    print(quantity)

    if request.method == 'POST':
        order_form = OrderForm(request.POST)
        if order_form.is_valid():
            # Store all billing information inside the Order table
            data = Order()
            data.user = current_user
            print(data.user)
            data.first_name = order_form.cleaned_data['first_name']
            print(data.first_name)
            data.last_name = order_form.cleaned_data['last_name']
            print(data.last_name)
            data.phone = order_form.cleaned_data['phone']
            print(data.phone)
            data.email = current_user.email
            print(data.email)
            data.payment_method = order_form.cleaned_data['payment_method']
            data.delivery_method = order_form.cleaned_data['delivery_method']
            data.delivery_address = order_form.cleaned_data['delivery_address']
            print(data.delivery_address)
            data.city = order_form.cleaned_data['city']
            print(data.city)
            data.order_note = order_form.cleaned_data['order_note']
            data.ip = request.META.get('REMOTE_ADDR')
            print(data.ip)
            data.order_total = total
            data.save()
            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            print(data.order_number)
            data.save()
            

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            order.is_ordered = True
            order.save()


            # Move the cart items to OrderProduct table
            cart_items = CartItem.objects.filter(user=request.user)

            for item in cart_items:
                orderproduct = OrderProduct()
                orderproduct.order_id = order.id
                orderproduct.user_id = request.user.id
                orderproduct.product_id = item.product_id
                orderproduct.quantity = item.quantity
                orderproduct.product_price = item.discounted_price
                # orderproduct.ordered = True
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
            ordered_products = OrderProduct.objects.filter(order_id=order.id)

            context = {
                'order': order,
                "total": total,
                "order_number": order.order_number,
                "ordered_products": ordered_products,
            }

            return render(request, 'orders/order_complete.html', context)



        else:
            print(order_form.errors)
            context = {
                'order_form': OrderForm(request.POST),
                }
            return render(request, 'store/checkout.html', context)

    else:
        
        order_form = OrderForm(request.POST or None)
        context = {
            'order_form': order_form,
        }

        return render(request, 'store/checkout.html', context)
    

def payments(request):
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    # user_payments = Payment.objects.filter(order__in=user_orders).order_by('-payment_date')
    order_data = []

    for order in user_orders:
        payments = Payment.objects.filter(order=order, amount_paid__gt=0).order_by('payment_date')
        remaining_balance = order.order_total
        payment_data = []

        for payment in payments:
            remaining_balance -= payment.amount_paid
            payment_data.append({
                'payment': payment,
                'remaining_balance': remaining_balance,
            })

        order_data.append ({
            'order': order,
            'payment_data': payment_data,
        })
    
    context = {
        'order_data': order_data
    }
    print(order_data)
    return render(request, 'orders/payments.html', context)
    


