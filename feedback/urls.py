from django.urls import path
from . import views

app_name = 'feedback'

urlpatterns = [
    path('submit/', views.submit_feedback, name='submit_feedback'),
    path('quick/<int:order_id>/', views.submit_quick_feedback, name='submit_quick_feedback'),
    path('form/', views.feedback_form_view, name='feedback_form'),
]
