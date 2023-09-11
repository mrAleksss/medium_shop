from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ReviewRating, ProductGallery, PriceTier, BicycleCharacteristics
from category.models import Category
from django.db.models import Q, Max, F, Subquery, OuterRef
from djmoney.money import Money
from djmoney.contrib.exchange.models import convert_money
from decimal import Decimal, InvalidOperation

from carts.views import _cart_id
from carts.models import CartItem
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

from .forms import ReviewForm, PriceRangeForm
from django.contrib import messages
from orders.models import OrderProduct

from django.http import JsonResponse


def char_endpoint(request):
    try:
        bicycles = Product.objects.all()
        product_code = request.GET.get('productCode')
        for bicycle in bicycles:
            try:
                bicycle_characteristics = BicycleCharacteristics.objects.get(bicycle__product_code=product_code)
                print(bicycle_characteristics)
                characteristics_dict = {
                    'bicycle_code': bicycle.product_code,
                    'wheel_diameter': bicycle_characteristics.wheel_diameter,
                    'brake_type': bicycle_characteristics.brake_type,
                    'frame_material': bicycle_characteristics.frame_material,
                    'frame_size': bicycle_characteristics.frame_size,
                    'weight': bicycle_characteristics.weight,
                    'rear_derailleur': bicycle_characteristics.rear_derailleur,
                    'gear_shifter': bicycle_characteristics.gear_shifter,
                    'fork': bicycle_characteristics.fork,
                    'cassete_ratchet': bicycle_characteristics.cassete_ratchet,
                    'crank': bicycle_characteristics.crank,
                    'speed_count': bicycle_characteristics.speed_count,
                    'wheel_rear_hub': bicycle_characteristics.wheel_rear_hub,
                    'wheel_front_hub': bicycle_characteristics.wheel_front_hub
                }
                print(characteristics_dict['bicycle_code'])
                return JsonResponse({'characteristics': characteristics_dict})
            except BicycleCharacteristics.DoesNotExist:
                print(f"Characteristics not found for bicycle with ID {bicycle.id}")

        return JsonResponse({'error': 'Характеристики не знайдені для данного велосипеда'}, status=404)

    except Product.DoesNotExist:
        return JsonResponse({'error': 'Велосипеды не найдены'}, status=404)
    



def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        category = get_object_or_404(Category, slug=category_slug)
        # products = Product.objects.filter(category=category, is_available=True)
        max_discount_subquery = PriceTier.objects.filter(product=OuterRef('pk')).order_by('-discount').values('discount', 'min_quantity')[:1]
        products = Product.objects.filter(category=category, is_available=True).annotate(max_discount=Subquery(max_discount_subquery.values('discount')), min_quantity=Subquery(max_discount_subquery.values('min_quantity'))).annotate(
            discounted_price=F('price_in_uah') - (F('price_in_uah') * F('max_discount') / 100)
        )

        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        products_count = products.count()
    else:
        max_discount_subquery = PriceTier.objects.filter(product=OuterRef('pk')).order_by('-discount').values('discount', 'min_quantity')[:1]
        products = Product.objects.filter(is_available=True).annotate(max_discount=Subquery(max_discount_subquery.values('discount')), min_quantity=Subquery(max_discount_subquery.values('min_quantity'))).annotate(
            discounted_price=F('price_in_uah') - (F('price_in_uah') * F('max_discount') / 100)
        )


        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        products_count = products.count()

    context = {
        "products": paged_products,
        "products_count": products_count,
    }

    return render(request, "store/store.html", context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
        price_tiers = single_product.tier.all()
        discounted_prices = []
        for tier in price_tiers:
            price = single_product.price_in_uah.amount
            discounted_price = price * (1 - tier.discount / 100)

            discounted_prices.append({'tier': tier, 'discounted_price': discounted_price})
        print(discounted_prices)

        
    except Exception as e:
        raise e
    
    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

    # Get the reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True).select_related('user__userprofile')

    # Get the product_gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)


    context = {
        "single_product": single_product,
        "in_cart": in_cart,
        "orderproduct": orderproduct,
        "reviews": reviews,
        "product_gallery": product_gallery,
        "price_tiers": price_tiers,
        "discounted_prices": discounted_prices
    }

    return render(request, "store/product_detail.html", context)


def search(request):

    products_count = 0
    price_form = PriceRangeForm()

    if request.method == 'GET':
        price_form = PriceRangeForm(request.GET)
        products = []
        if 'keyword' in request.GET:
            keyword = request.GET['keyword']
            if keyword:
                products = Product.objects.order_by("-created_date").filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
                products_count = products.count()
        elif price_form.is_valid():
            min_price = price_form.cleaned_data['min_price']
            min_price = Decimal(min_price)
            max_price = price_form.cleaned_data['max_price']
            max_price = Decimal(max_price)
            products = Product.objects.filter(price_in_uah__gte=min_price, price_in_uah__lte=max_price)

            products_count = products.count()
        else:
            products = []
    

    context = {
        "products": products,
        "products_count": products_count,
        "form": price_form,
    }

    return render(request, "store/store.html", context)


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, "Дякуємо! Ваші відгуки було обновлено...")
            return redirect(url)

        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.review = form.cleaned_data['review']
                data.rating = form.cleaned_data['rating']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, "Дякуємо, ваш відгук було надіслано.")
                return redirect(url)
            

def contacts(request):
    return render(request, "store/contacts.html")


def info(request):
    return render(request, "store/info.html")


def about(request):
    return render(request, "store/about.html")


def return_info(request):
    return render(request, "store/return_info.html")
























