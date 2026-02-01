from django.urls import path
from . import views

app_name= "dashboard"

urlpatterns = [

    path('', views.dashboard_home_view, name="dashboard_home_view"),
    path('login/', views.dashboard_login_view, name="dashboard_login_view"),
    path('events/', views.dashboard_events_view, name="dashboard_events_view"),
    path('requests/', views.dashboard_requests_view, name="dashboard_requests_view"),
    path("requests/<id>/delete", views.dashboard_request_delete_view, name="dashboard_request_delete_view"),
    path("requests/<id>/reject", views.dashboard_request_reject_view, name="dashboard_request_reject_view"),
    path("requests/<id>/accept", views.dashboard_request_accept_view, name="dashboard_request_accept_view"),
    path('admins/', views.dashboard_admins_view, name="dashboard_admins_view"),
    path('admins/<id>/delete/', views.dashboard_admin_delete_view, name="dashboard_admin_delete_view"),
    path('events/<id>/delete/', views.dashboard_event_delete_view, name="dashboard_event_delete_view"),
    path('events/<id>/request_status', views.dashboard_event_request_status_view, name="dashboard_event_request_status_view"),
    path('events/attend_requests', views.dashboard_attend_request_view, name="dashboard_attend_request_view"),
    path('logout/',views.dashboard_logout_view, name="dashboard_logout_view"),
    path('events/<id>/edit/', views.dashboard_event_edit_view, name="dashboard_event_edit_view"),
    path('events/<id>/requests/', views.dashboard_event_requests_view, name="dashboard_event_requests_view"),
    path('ratings/', views.dashboard_ratings_view, name="dashboard_ratings_view"),
    path('users/', views.dashboard_users_view, name="dashboard_users_view"),
    path('users/<id>/delete', views.dashboard_users_delete_view, name="dashboard_users_delete_view"),
    path('users/<id>/requests', views.dashboard_user_requests_view, name="dashboard_user_requests_view"),
    path('ratings/', views.dashboard_ratings_view, name="dashboard_ratings_view"),
    path('ratings/<id>/delete/', views.dashboard_ratings_delete_view, name="dashboard_ratings_delete_view"),
    path('ratings/<id>/update_status/', views.dashboard_ratings_update_status_view, name="dashboard_ratings_update_status_view"),
    path('ai_recommendations/', views.ai_recommendations_view, name="ai_recommendations_view")

]