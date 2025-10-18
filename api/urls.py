from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'groups', views.GroupViewSet, basename='group')
router.register(r'expenses', views.ExpenseViewSet, basename='expense')
router.register(r'payments', views.PaymentViewSet, basename='payment')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    
    # User endpoints
    path('users/me/', views.user_me, name='user-me'),
    path('users/profile/', views.UserProfileView.as_view(), name='user-profile'),
    
    # Smart split endpoint
    path('ai/smart-split/', views.smart_split, name='smart-split'),
    
    # Test/Simulation endpoints
    path('test/simulate-stk-push/', views.simulate_stk_push, name='simulate-stk-push'),
    path('test/simulate-expense-payments/', views.simulate_expense_payments, name='simulate-expense-payments'),
    
    # Webhook endpoint
    path('payhero/webhook/', views.payhero_webhook, name='payhero-webhook'),
]
