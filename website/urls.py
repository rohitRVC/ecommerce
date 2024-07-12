from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [    
    path('', views.index, name='index'),
    path('index', views.index, name='index'),
    path('categories/', views.categories, name='categories'),
    path('products/', views.products, name='products'),
    path('contact/', views.contact, name='contact'),
    path('cart/', views.cart, name='cart'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update_cart_quantity/<int:item_id>/<str:action>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('about/', views.about, name='about'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),
    path('account/', views.account_view, name='account'),
    path('orders/', views.orders_view, name='orders'),
    path('logout/', views.logout_view, name='logout'),
    path('admin_home/', views.admin_home, name='admin_home'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin_categories/', views.admin_categories, name='admin_categories'),
    path('admin_categories/update/<int:pk>/', views.admin_update_category, name='admin_update_category'),
    path('admin_categories/delete/<int:pk>/', views.admin_delete_category, name='admin_delete_category'),
    path('admin_products/', views.admin_products, name='admin_products'),
    path('admin_add_product/', views.admin_add_product, name='admin_add_product'),
    path('admin_update_product/update/<int:pk>/', views.admin_update_product, name='admin_update_product'),
    path('admin_delete_product/delete/<int:pk>/', views.admin_delete_product, name='admin_delete_product'),
    path('admin_users/', views.admin_users, name='admin_users'),
    # path('categories/', views.add_category, name='categories'),
    path('product_details/<int:pk>/', views.product_details, name='product_details'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)