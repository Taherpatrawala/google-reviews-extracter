from .views import getReviewsOld
from django.urls import path

urlpatterns = [
    # path('getReviews/', getReviews, name='getReviews'),
    path('getReviewsOld/', getReviewsOld, name='getReviewsOld'),
]
