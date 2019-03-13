
import haystack
from django.conf.urls import include, url
from django.contrib import admin

from orders import views

urlpatterns = [
    url(r'^place$', views.PlaceOrdereView.as_view(),name='place'),
]
