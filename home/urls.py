from django.urls import path
from . import views

app_name= 'home'

urlpatterns = [
    path('', views.home_view, name="home_view"),
    path('login/', views.login_view, name="login_view"),
    path('register/', views.register_view, name="register_view"),
    path('events/', views.events_view, name="events_view"),
    path('event/<id>', views.event_details_view, name="event_details_view"),
    path('book_event/<id>', views.book_event_request, name="book_event_request"),
    path('logout/',views.home_logout_view, name="home_logout_view"),
    path('requests/',views.requests_view, name="requests_view"),
    path('requests/<id>/cancel',views.cancel_request_view, name="cancel_request_view"),
    path('rating_event/<id>',views.add_rating_for_event, name="add_rating_for_event"),
    path('profile/',views.profile_view, name="profile_view"),
    path('change_password/', views.change_password, name="change_password")

]