from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_reviews, name='admin_reviews'),
    path('reviews/delete/<int:review_id>/', views.delete_review, name='delete_review'),
]
