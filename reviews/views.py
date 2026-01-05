from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Avg

from .models import Review, ReviewHelpful
from store.models import Product


@login_required
@require_POST
def add_review(request, product_slug):
    """Add a review for a product."""
    product = get_object_or_404(Product, slug=product_slug)
    
    # Check if user already reviewed this product
    if Review.objects.filter(product=product, user=request.user).exists():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False, 
                'error': 'You have already reviewed this product.'
            }, status=400)
        messages.error(request, 'You have already reviewed this product.')
        return redirect('store:product_detail', slug=product_slug)
    
    # Get form data
    rating = request.POST.get('rating')
    title = request.POST.get('title', '')
    comment = request.POST.get('comment', '')
    longevity_rating = request.POST.get('longevity_rating')
    sillage_rating = request.POST.get('sillage_rating')
    value_rating = request.POST.get('value_rating')
    
    # Validate rating
    try:
        rating = int(rating)
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")
    except (TypeError, ValueError):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False, 
                'error': 'Please provide a valid rating (1-5 stars).'
            }, status=400)
        messages.error(request, 'Please provide a valid rating.')
        return redirect('store:product_detail', slug=product_slug)
    
    # Validate comment
    if not comment.strip():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False, 
                'error': 'Please write a review comment.'
            }, status=400)
        messages.error(request, 'Please write a review comment.')
        return redirect('store:product_detail', slug=product_slug)
    
    # Create review
    review = Review(
        product=product,
        user=request.user,
        rating=rating,
        title=title,
        comment=comment,
    )
    
    # Add optional ratings
    if longevity_rating:
        try:
            review.longevity_rating = int(longevity_rating)
        except ValueError:
            pass
    if sillage_rating:
        try:
            review.sillage_rating = int(sillage_rating)
        except ValueError:
            pass
    if value_rating:
        try:
            review.value_rating = int(value_rating)
        except ValueError:
            pass
    
    review.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Thank you for your review!',
            'review': {
                'id': review.id,
                'rating': review.rating,
                'title': review.title,
                'comment': review.comment,
                'user_name': request.user.get_full_name() or request.user.email.split('@')[0],
                'verified_purchase': review.verified_purchase,
                'created_at': review.created_at.strftime('%B %d, %Y'),
            },
            'product_stats': {
                'average_rating': float(product.average_rating),
                'review_count': product.review_count,
            }
        })
    
    messages.success(request, 'Thank you for your review!')
    return redirect('store:product_detail', slug=product_slug)


@login_required
@require_POST
def edit_review(request, review_id):
    """Edit user's own review."""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    rating = request.POST.get('rating')
    title = request.POST.get('title', '')
    comment = request.POST.get('comment', '')
    
    try:
        rating = int(rating)
        if not 1 <= rating <= 5:
            raise ValueError()
    except (TypeError, ValueError):
        messages.error(request, 'Please provide a valid rating.')
        return redirect('store:product_detail', slug=review.product.slug)
    
    if not comment.strip():
        messages.error(request, 'Please write a review comment.')
        return redirect('store:product_detail', slug=review.product.slug)
    
    review.rating = rating
    review.title = title
    review.comment = comment
    
    # Update optional ratings
    longevity_rating = request.POST.get('longevity_rating')
    sillage_rating = request.POST.get('sillage_rating')
    value_rating = request.POST.get('value_rating')
    
    if longevity_rating:
        try:
            review.longevity_rating = int(longevity_rating)
        except ValueError:
            pass
    if sillage_rating:
        try:
            review.sillage_rating = int(sillage_rating)
        except ValueError:
            pass
    if value_rating:
        try:
            review.value_rating = int(value_rating)
        except ValueError:
            pass
    
    review.save()
    messages.success(request, 'Your review has been updated.')
    return redirect('store:product_detail', slug=review.product.slug)


@login_required
@require_POST
def delete_review(request, review_id):
    """Delete user's own review."""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    product_slug = review.product.slug
    product = review.product
    review.delete()
    
    # Update product rating
    product.update_rating()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Review deleted successfully.',
            'product_stats': {
                'average_rating': float(product.average_rating),
                'review_count': product.review_count,
            }
        })
    
    messages.success(request, 'Your review has been deleted.')
    return redirect('store:product_detail', slug=product_slug)


@login_required
@require_POST
def mark_helpful(request, review_id):
    """Mark a review as helpful."""
    review = get_object_or_404(Review, id=review_id)
    
    # Can't mark own review as helpful
    if review.user == request.user:
        return JsonResponse({
            'success': False,
            'error': "You can't mark your own review as helpful."
        }, status=400)
    
    # Check if already marked
    helpful, created = ReviewHelpful.objects.get_or_create(
        review=review,
        user=request.user
    )
    
    if created:
        review.helpful_count += 1
        review.save(update_fields=['helpful_count'])
        return JsonResponse({
            'success': True,
            'helpful_count': review.helpful_count,
            'message': 'Marked as helpful!'
        })
    else:
        # Toggle off
        helpful.delete()
        review.helpful_count = max(0, review.helpful_count - 1)
        review.save(update_fields=['helpful_count'])
        return JsonResponse({
            'success': True,
            'helpful_count': review.helpful_count,
            'message': 'Removed helpful vote.'
        })


def product_reviews(request, product_slug):
    """Get paginated reviews for a product (AJAX)."""
    product = get_object_or_404(Product, slug=product_slug)
    reviews = product.reviews.filter(is_approved=True).select_related('user')
    
    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'oldest':
        reviews = reviews.order_by('created_at')
    elif sort_by == 'highest':
        reviews = reviews.order_by('-rating', '-created_at')
    elif sort_by == 'lowest':
        reviews = reviews.order_by('rating', '-created_at')
    elif sort_by == 'helpful':
        reviews = reviews.order_by('-helpful_count', '-created_at')
    else:  # newest
        reviews = reviews.order_by('-created_at')
    
    # Filter by rating
    rating_filter = request.GET.get('rating')
    if rating_filter:
        try:
            rating_filter = int(rating_filter)
            reviews = reviews.filter(rating=rating_filter)
        except ValueError:
            pass
    
    # Pagination
    paginator = Paginator(reviews, 5)
    page = request.GET.get('page', 1)
    reviews_page = paginator.get_page(page)
    
    # Calculate rating breakdown
    rating_breakdown = {}
    all_reviews = product.reviews.filter(is_approved=True)
    total = all_reviews.count()
    for i in range(1, 6):
        count = all_reviews.filter(rating=i).count()
        rating_breakdown[i] = {
            'count': count,
            'percentage': round((count / total * 100) if total > 0 else 0)
        }
    
    context = {
        'product': product,
        'reviews': reviews_page,
        'rating_breakdown': rating_breakdown,
        'sort_by': sort_by,
        'rating_filter': rating_filter,
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        html = render_to_string('reviews/_review_list.html', context, request=request)
        return JsonResponse({
            'html': html,
            'has_next': reviews_page.has_next(),
            'total_pages': paginator.num_pages,
            'current_page': reviews_page.number,
        })
    
    return render(request, 'reviews/product_reviews.html', context)
