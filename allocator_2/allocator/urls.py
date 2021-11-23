from django.urls import path
from allocator.views import request_allocation

urlpatterns = [
    path("request-allocation/", request_allocation),
    path("check-allocation/", request_allocation),
]
