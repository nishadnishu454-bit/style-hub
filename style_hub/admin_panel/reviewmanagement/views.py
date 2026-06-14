from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from user.orders.models import Review


def is_admin(user):
    return user.is_authenticated and user.is_staff


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def admin_reviews(request):

    search = request.GET.get('search', '').strip()
    rating_filter = request.GET.get('rating', '').strip()

    reviews = Review.objects.select_related(
        'user',
        'product'
    ).order_by('-created_at')

    # SEARCH FILTER
    if search:

        reviews = reviews.filter(

            Q(product__product_name__icontains=search) |

            Q(user__username__icontains=search) |

            Q(title__icontains=search) |

            Q(content__icontains=search)

        )

    # RATING FILTER
    if rating_filter:

        try:

            reviews = reviews.filter(
                rating=int(rating_filter)
            )

        except ValueError:
            pass

    # PAGINATION
    paginator = Paginator(reviews, 10)

    page_number = request.GET.get('page')

    reviews_page = paginator.get_page(page_number)

    context = {
        'reviews': reviews_page,
        'search': search,
        'rating_filter': rating_filter,
    }

    return render(
        request,
        'reviews_listing.html',
        context
    )


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_review(request, review_id):

    review = get_object_or_404(
        Review,
        id=review_id
    )

    review.delete()

    messages.success(
        request,
        'Review deleted successfully'
    )

    return redirect('admin_reviews')