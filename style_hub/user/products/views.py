from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from admin_panel.productmanagement.models import Product
from admin_panel.variantmanagement.models import ProductVariant
from admin_panel.categorymanagement.models import Category
from user.cart.models import Cart
from user.whishlist.models import Wishlist
from django.db.models import Q,Min,Count,Avg
from django.contrib import messages
from decimal import Decimal




def product_page(request):
    sort = request.GET.get('sort', '')
    search = request.GET.get('search', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    category_id = request.GET.get('category')

    products = Product.objects.filter(
        is_deleted=False,
        is_active=True,
        category__is_deleted=False,
        category__is_active=True,
        variants__is_deleted=False,
        variants__is_active=True
    ).select_related(
        'category'
    ).annotate(
        display_price=Min('variants__variant_price'),
        review_count=Count('reviews', distinct=True),
        avg_rating=Avg('reviews__rating')
    ).prefetch_related(
        'variants',
        'variants__images'
    )

    categories = Category.objects.filter(
        is_deleted=False,
        is_active=True
    )

    if search:
        products = products.filter(
            Q(product_name__icontains=search) |
            Q(description__icontains=search) |
            Q(category__category_name__icontains=search)
        )

    if category_id:
        products = products.filter(category__id=category_id)

    if min_price:
        products = products.filter(variants__variant_price__gte=min_price)

    if max_price:
        products = products.filter(variants__variant_price__lte=max_price)

    if sort == 'price_low':
        products = products.order_by('display_price')
    elif sort == 'price_high':
        products = products.order_by('-display_price')
    elif sort == 'a_z':
        products = products.order_by('product_name')
    elif sort == 'z_a':
        products = products.order_by('-product_name')
    else:
        products = products.order_by('-id')

    products = products.distinct()

    for product in products:
        variant = product.variants.filter(
            is_deleted=False,
            is_active=True
        ).first()

        product.display_variant = variant

        if variant:
            product.display_price = variant.offer_price
            product.display_image = variant.images.filter(is_primary=True).first()

            if not product.display_image:
                product.display_image = variant.images.first()
        else:
            product.display_image = None
            product.display_price = Decimal('0.00')


    wishlist_variant_ids = []
    if request.user.is_authenticated:
        wishlist_variant_ids = list(Wishlist.objects.filter(user=request.user).values_list('variant_id', flat=True))

   

    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)
  

    context = {
        'products': products_page,
        'categories': categories,
        'category_id': category_id,
        'sort': sort,
        'search': search,
        'min_price': min_price,
        'max_price': max_price,
        'wishlist_variant_ids': wishlist_variant_ids,
        
        
    }
   
    return render(request, 'product_page.html', context)



def product_detail(request, id):
    product = get_object_or_404(
        Product,
        id=id,
        is_deleted=False,
        is_active=True,
        category__is_deleted=False,
        category__is_active=True,
    )

    variants = product.variants.filter(
        is_deleted=False,
        is_active=True
    ).prefetch_related('images')

    if not variants.exists():
        return redirect('product_page')

    reviews = product.reviews.select_related('user', 'order_item', 'order_item__variant').prefetch_related('images').order_by('-created_at')
    
    review_count = reviews.count()
    if review_count > 0:
        average_rating = sum([r.rating for r in reviews]) / review_count
    else:
        average_rating = 0

    related_products = Product.objects.filter(
        category=product.category,
        is_deleted=False,
        is_active=True,
        category__is_deleted=False,
        category__is_active=True,
        variants__is_deleted=False,
        variants__is_active=True
    ).exclude(id=product.id).distinct()[:4]



    wishlist_variant_ids = []

    if request.user.is_authenticated:
        wishlist_variant_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list('variant_id', flat=True)

    for variant in variants:
        variant.is_wishlisted = variant.id in wishlist_variant_ids

    context = {
        'product': product,
        'variants': variants,
        'related_products': related_products,
        'reviews': reviews,
        'review_count': review_count,
        'average_rating': average_rating,
        'average_rating_range': range(int(average_rating)),
        'empty_rating_range': range(5 - int(average_rating)),
    }
    return render(request, 'product_detial.html', context)




@login_required(login_url='login')
def buy_now(request):
    variant_id = request.GET.get('variant_id')
    variant = get_object_or_404(
        ProductVariant,
        id=variant_id,
        is_deleted=False,
        is_active=True
    )
    if variant.variant_stock <= 0:
        messages.error(request, 'Product out of stock')
        return redirect('product_detail', id=variant.product.id)

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        variant=variant,
        defaults={
            'quantity': 1
        }
    )

    if not created:
        cart_item.quantity = 1
        cart_item.save()

    return redirect('checkout')