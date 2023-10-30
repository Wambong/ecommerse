from django.urls import path
from . import views
urlpatterns = [
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('register', views.register, name='register'),
    path('profile',views.profile, name='profile'),
    path('', views.messages_page, name = "chat"),
    path('create_thread/<str:username>/', views.create_thread, name='create_thread'),
    path('view_thread/<int:thread_id>/', views.view_thread, name='view_thread'),
]
