from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.landing_page, name='tampilandepan'),  # Tambahkan ini untuk landing page
    path('chatbot/', views.templatechatbot, name='templatechatbot'),
    path('register/', views.register, name='register'),
    path('register/success/', views.register_success, name='register_success'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('riwayat/', views.riwayat_view, name='riwayat'),
    path('artikel/', views.artikel_view, name='artikel'),
    path('logout/', views.logout_view, name='logout'),
]

