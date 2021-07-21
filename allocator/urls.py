from django.urls import path
from .views import index, request_allocation

urlpatterns = [
    path('', index),
    path('request-allocation/', request_allocation),
]
