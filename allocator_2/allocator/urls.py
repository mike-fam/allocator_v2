from django.urls import path
from .views import get_allocation, request_allocation

urlpatterns = [
    path('get-allocation/<str:token>/', get_allocation),
    path('request-allocation/', request_allocation),
]
