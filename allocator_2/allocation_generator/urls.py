from django.urls import path
from . import views

urlpatterns = [
    path('get-allocation/<str:token>/', views.get_allocation,
         name='get-allocation'),
    path('request-allocation/', views.request_allocation,
         name='request-allocation'),
]
