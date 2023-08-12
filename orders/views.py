from django.shortcuts import render, redirect
import datetime
from carts.models import CartItem
from .forms import OrderForm
from .models import Order, Payment, OrderProduct
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
# pdf imports
from django.contrib.auth.decorators import login_required
from accounts.views import generate_pdf


def place_order(request, total=0, quantity=0):
    # take current user that are registered in system
    current_user = request.user
    # if cart_count is less or equal to 0 then redirect to shop 
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect("store")

    for cart_item in cart_items:
        # Count total price by discounted method in CartItem and also count quantity
        total += cart_item.discounted_price*cart_item.quantity
        quantity += cart_item.quantity


    if request.method == 'POST':
        order_form = OrderForm(request.POST)
        if order_form.is_valid():
            # Create instance of Order and record all neccessary information before saving
            data = Order()
            data.user = current_user
            data.first_name = order_form.cleaned_data['first_name']
            data.last_name = order_form.cleaned_data['last_name']
            data.phone = order_form.cleaned_data['phone']
            data.email = current_user.email
            data.payment_method = order_form.cleaned_data['payment_method']
            data.delivery_method = order_form.cleaned_data['delivery_method']
            data.delivery_address = order_form.cleaned_data['delivery_address']
            data.city = order_form.cleaned_data['city']
            data.order_note = order_form.cleaned_data['order_note']
            data.ip = request.META.get('REMOTE_ADDR')
            data.order_total = total
            data.save()
            # Generate order number based on order.id that was generating after data.save()
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            
            # Move the cart items to OrderProduct table
            cart_items = CartItem.objects.filter(user=request.user)

            for item in cart_items:
                orderproduct = OrderProduct()
                orderproduct.order_id = order.id
                orderproduct.user_id = request.user.id
                orderproduct.product_id = item.product_id
                orderproduct.quantity = item.quantity
                orderproduct.product_price = item.discounted_price
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
            # generate the PDF using the existing view
            pdf_file = generate_pdf(request, order.order_number)

            # Clear cart
            CartItem.objects.filter(user=request.user).delete()

            # Send order recieved email to customer
            mail_subject = "Дякуємо за ваше замовлення!"
            message = render_to_string('orders/order_recieved_email.html', {
                        'user': request.user,
                        'order': order,
                    })
            to_email = request.user.email
            pdf_filename = 'packing_list.pdf'
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.attach(pdf_filename, pdf_file.getvalue(), 'application/pdf')
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
            return render(request, 'store/checkout.html', {'order_form': order_form})

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
        # Retrieve all payments greater then 0 from all users orders 
        payments = Payment.objects.filter(order=order, amount_paid__gt=0).order_by('-payment_date')
        remaining_balance = order.order_total
        # Create list for appending data with payment instance and remaining_balance
        payment_data = []

        for payment in payments:
            # Asign new value for variable remaining_balance according its equal -amount_paid for every payment instance
            remaining_balance -= payment.amount_paid
            # append newly creating data about balance with payment
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

    return render(request, 'orders/payments.html', context)
