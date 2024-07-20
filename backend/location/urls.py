from django.urls import path
from . import views

app_name = 'location'
urlpatterns = [
    path('states/', views.GetLocation.as_view(), name="states"),
]
