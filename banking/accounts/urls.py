from django.urls import path
from . import views
from .views import register, LoginView
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('deposit/', views.deposit_view, name='deposit'),
    path('withdraw/', views.withdraw_view, name='withdraw'),
    path('transfer/', views.transfer_view, name='transfer'),
    path('airtime/', views.buy_airtime, name='buy_airtime'),
    path('data/', views.buy_data, name='buy_data'),
    path('tv/', views.tv_view, name='pay_tv'),
    path('electricity/', views.pay_electricity, name='pay_electricity'),
    path('kyc-upload/', views.kyc_upload_view, name='kyc_upload'),
    path('transactions/', views.transaction_history_view, name='transaction_history'),
    path('manage-cards/', views.manage_cards, name='manage_cards'),
    path('approve-transactions/', views.approve_transactions_view, name='approve_transactions'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('register/', views.register, name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('accounts/upload-picture/', views.update_profile_picture, name='update_profile_picture'),

]
