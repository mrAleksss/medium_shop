from django.shortcuts import render, redirect, get_object_or_404
from . forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
# Verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string, get_template
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from carts.views import _cart_id
from carts.models import Cart, CartItem
import requests

from orders.models import Order, OrderProduct

from django.http import HttpResponse
from weasyprint import HTML
from io import BytesIO


def register(request):
    if request.method == 'POST': 
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.save()

            # User activation
            current_site = get_current_site(request)
            mail_subject = "Будь-ласка активуйте свій акаунт"
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            # messages.success(request, "Дякуємо за реєстрацію. Ми вислали на ваш e-mail посилання для його підтвердження. Перевірте ваш e-mail та перейдіть за посиланням")

            return redirect("/accounts/login?command=verification&email="+email)
    else:
        form = RegistrationForm()

    context = {
        "form": form
    }
    return render(request, 'accounts/register.html', context)


def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)

                    # Getting the product variations by cart id:
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    # Get the cart item from the user to access his product variations
                    cart_item = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)

                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
            except:
                pass
            auth.login(request, user)
            messages.success(request, 'Вхід виконано')
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)      
            except:
                return redirect('dashboard')
        else:
            messages.error(request, 'Неправильно введенні данні')
            return redirect('login')

    return render(request, 'accounts/login.html')


@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'Ви вийшли з облікового запису')
    return redirect('login')


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Вітаємо! Ваш акаунт Активовано")
        return redirect("login")
    else:
        messages.error(request, "Invalid Activation Link")
        return render("register")
    

@login_required(login_url='login')
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
    orders_count = orders.count()

    userprofile = UserProfile.objects.get(user_id=request.user.id)
    context = {
        "orders_count": orders_count,
        "userprofile": userprofile,
    }
    return render(request, 'accounts/dashboard.html', context)


def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__iexact=email)

            # Reset password email
            current_site = get_current_site(request)
            mail_subject = "Змініть свій пароль"
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send() 

            messages.success(request, 'Посилання для зміни пароля було надіслане на ваш email') 
            return redirect('login')        

        else:
            messages.error(request, 'Такого Акаунту не існує')
            return redirect("forgotPassword")
        
    return render(request, 'accounts/forgotPassword.html')


def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, "Будь-ласка, змініть свій пароль")
        return redirect("resetPassword")
    else:
        messages.error(request, "This link has been expired!")
        return redirect("login")
    

def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, "Пароль змінено успішно!")
            return redirect("login")

        else:
            messages.error(request, "Паролі не співпадають!")
            return redirect("resetPassword")
    else:
        return render(request, 'accounts/resetPassword.html')


@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user).exclude(status='Скасовано').order_by('-created_at')
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        action = request.POST.get('action')

        if action == 'discard':
            order_to_discard = Order.objects.get(id=order_id)
            order_to_discard.status = 'Скасовано'
            order_to_discard.save()
            messages.success(request, f'замовлення {order_to_discard.order_number} успішно "Скасовано"')

    context = {
        "orders": orders,
    }
    return render(request, 'accounts/my_orders.html', context)


@login_required(login_url='login')
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated!")
            return redirect("edit_profile")
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile,
    }

    return render(request, 'accounts/edit_profile.html', context)


@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(username__exact=request.user.username)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                # auth.logout(request)
                messages.success(request, "Password updated successfully")
                return redirect('change_password')
            else:
                messages.error(request, 'Please enter valid current password')
                return redirect('change_password')
        else:
            messages.error(request, 'Password does not match')
            return redirect('change_password')

    return render(request, 'accounts/change_password.html')


@login_required(login_url='login')
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    
    for item in order_detail:
        item.subtotal = item.product_price * item.quantity

    context = {
        'order_detail': order_detail,
        'order': order,
    }

    return render(request, 'accounts/order_detail.html', context)


@login_required(login_url='login')
def generate_pdf(request, order_id):
    order = Order.objects.get(user=request.user, order_number=order_id)
    order_products = OrderProduct.objects.filter(order=order)
    for item in order_products:
        item.subtotal = item.product_price * item.quantity

    context = {
        'order': order,
        'order_products': order_products,
    }

    # html_string = render(request, 'accounts/order_pdf.html', context).content
    template = get_template('accounts/order_pdf.html')
    html_content = template.render(context)

    pdf_file = BytesIO()
    HTML(string=html_content).write_pdf(pdf_file)

    response = HttpResponse(pdf_file.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'filename="{order_id}.pdf"'

    return response







