from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('product/<slug:product_slug>/add/', views.add_review, name='add_review'),
    path('<int:review_id>/edit/', views.edit_review, name='edit_review'),
    path('<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('<int:review_id>/helpful/', views.mark_helpful, name='mark_helpful'),
    path('product/<slug:product_slug>/', views.product_reviews, name='product_reviews'),
]
