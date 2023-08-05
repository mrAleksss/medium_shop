from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ReviewRating, ProductGallery, PriceTier
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


def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        category = get_object_or_404(Category, slug=category_slug)
        # products = Product.objects.filter(category=category, is_available=True)
        max_discount_subquery = PriceTier.objects.filter(product=OuterRef('pk')).order_by('-discount').values('discount', 'min_quantity')[:1]
        products = Product.objects.filter(category=category, is_available=True).annotate(max_discount=Subquery(max_discount_subquery.values('discount')), min_quantity=Subquery(max_discount_subquery.values('min_quantity'))).annotate(
            discounted_price=F('price') - (F('price') * F('max_discount') / 100)
        )
        for product in products:
            try:
                discounted_price_usd = Money(Decimal(product.discounted_price), currency='USD')
                product.discounted_price_in_uah = convert_money(discounted_price_usd, 'UAH')
            except(InvalidOperation, TypeError):
                product.discounted_price_in_uah = None

        # get discount price 
        # for product in products:
        #     product.calculated_price = product.calculate_price

        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        products_count = products.count()
    else:
        # products = Product.objects.all().filter(is_available=True).order_by('id')
        # get discount price 
        # for product in products:
        #     product.calculated_price = product.calculate_price
        max_discount_subquery = PriceTier.objects.filter(product=OuterRef('pk')).order_by('-discount').values('discount', 'min_quantity')[:1]
        products = Product.objects.filter(is_available=True).annotate(max_discount=Subquery(max_discount_subquery.values('discount')), min_quantity=Subquery(max_discount_subquery.values('min_quantity'))).annotate(
            discounted_price=F('price') - (F('price') * F('max_discount') / 100)
        )
        for product in products:
            try:
                discounted_price_usd = Money(Decimal(product.discounted_price), currency='USD')
                product.discounted_price_in_uah = convert_money(discounted_price_usd, 'UAH')
            except(InvalidOperation, TypeError):
                product.discounted_price_in_uah = None


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
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    # Get the product_gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)


    context = {
        "single_product": single_product,
        "in_cart": in_cart,
        "orderproduct": orderproduct,
        "reviews": reviews,
        "product_gallery": product_gallery,
    }

    return render(request, "store/product_detail.html", context)


def search(request):

    products_count = 0

    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by("-created_date").filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            products_count = products.count()
    else:
        # handle the case if the user didnt provide valid input
        products = []


    form = PriceRangeForm(request.GET)
    print('began')
    if form.is_valid():
        
        min_price = form.cleaned_data['min_price']
        max_price = form.cleaned_data['max_price']
    # new addition
    # min_price = request.GET.get('min_price')
    # max_price = request.GET.get('max_price')
        print(f"form is valid{min_price}" and {max_price})
        if min_price:
            print(min_price)
            min_price = Decimal(min_price)
            print(type(min_price))
            products = Product.objects.filter(price__gte=min_price)
        else:
            products = Product.objects.all()

        if max_price:
            print(max_price)
            max_price = Decimal(max_price)
            print(max_price)
            products = Product.objects.filter(price__lte=max_price)
    else:
        products = Product.objects.all()
    

    context = {
        "products": products,
        "products_count": products_count,
        "form": form
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
























