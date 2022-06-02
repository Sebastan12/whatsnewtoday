from django.urls import path
from . import views

#url configuration
urlpatterns = [
    path('hello/', views.say_hello),
    path('scrape/', views.scrape),
    path('morethanone/', views.morethanone),
    path('filter/', views.filter)
]
