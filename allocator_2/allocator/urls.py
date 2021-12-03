from django.urls import path
from allocator.views import request_allocation, check_allocation

urlpatterns = [
    path("request-allocation/", request_allocation),
    path("check-allocation/<str:timetable_id>", check_allocation),
]
