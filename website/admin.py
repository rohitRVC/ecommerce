from django.contrib import admin

# Register your models here.

from .models import Category, Product, CartItem, Cart, Checkout, Order, OrderItem

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
admin.site.register(Category)

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name','category','price','description','image1','image2','image3','image4','image5','image6')
admin.site.register(Product)

class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart','product','quantity')
admin.site.register(CartItem)

class CartAdmin(admin.ModelAdmin):
    list_display = ('user','created_at')
admin.site.register(Cart)

class CheckoutAdmin(admin.ModelAdmin):
    list_display = ('user','address','city','state','zip_code','payment_method','payment_status')
admin.site.register(Checkout)

class OrderAdmin(admin.ModelAdmin):
    list_display = ('user','order_date', 'status')
admin.site.register(Order)

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity')
admin.site.register(OrderItem)