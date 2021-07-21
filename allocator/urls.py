from django.urls import path
from .views import get_allocation, request_allocation

urlpatterns = [
    path('get-allocation', get_allocation),
    path('request-allocation/<str:token>', request_allocation),
]
