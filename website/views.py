from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .forms import SignUpForm, SignInForm, ProductForm, CheckoutForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .decorators import login_required
from .models import Category, Product, CartItem, Cart, Checkout, Order, OrderItem
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone

# Create your views here.

User = get_user_model()

@login_required
def index(request):
    return render(request, 'index.html')

@login_required
def categories(request):
    categories = Category.objects.all()
    return render(request, 'categories.html', {'categories': categories})

@login_required
def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    return render(request, 'category_products.html', {'category': category, 'products': products})

@login_required
def products(request):
    products = Product.objects.all()
    # Pagination settings
    paginator = Paginator(products, 15)  # 15 products per page
    page = request.GET.get('page')
    try:
        products_paginated = paginator.page(page)
    except PageNotAnInteger:
        products_paginated = paginator.page(1)
    except EmptyPage:
        products_paginated = paginator.page(paginator.num_pages)
    return render(request, 'products.html', {'products': products_paginated})

def product_details(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_details.html', {'product': product})

def contact(request):
    return render(request, 'contact.html')

@login_required
def cart(request):
    user = request.user  # This should be a User instance
    cart, created = Cart.objects.get_or_create(user=user)
    cart_items = CartItem.objects.filter(cart=cart)
    context = {
        'cart_items': cart_items,
        'cart': cart
    }
    return render(request, 'cart.html', context)
    
@login_required  
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1  # Add selected quantity to existing cart item
   
    cart_item.save()
    return redirect('cart')


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    return redirect('cart')

@login_required
def update_cart_quantity(request, item_id, action):
    cart_item = get_object_or_404(CartItem, id=item_id)
    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease' and cart_item.quantity > 1:
        cart_item.quantity -= 1
    cart_item.save()
    return redirect('cart')

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            checkout_instance = form.save(commit=False)
            checkout_instance.user = request.user
            checkout_instance.save()

            # Prepare products data for JSONField
            products_data = []
            for item in cart_items:
                products_data.append({
                    'product_name': item.product.name,
                    'quantity': item.quantity
                })

            # Create the Order
            order = Order.objects.create(
                user=request.user,
                status='Pending',
                order_date=timezone.now(),
                products=products_data  # Store products data as JSON
            )

            # Clear the cart
            cart_items.delete()

            messages.success(request, 'Your order has been placed successfully!')
            return redirect('orders_view')
    else:
        form = CheckoutForm()

    context = {
        'form': form,
        'cart_items': cart_items,
        'total_price': cart.total_amount()
    }
    return render(request, 'checkout.html', context)

def about(request):
    return render(request, 'about.html')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('signin')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def signin(request):
    if request.method == 'POST':
        form = SignInForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_superuser:
                return redirect('admin_home')
            else:
                return redirect('index')
    else:
        form = SignInForm()
    return render(request, 'signin.html', {'form': form})

@login_required
def signout(request):
    logout(request)
    return redirect('signin')

# def home(request):
#     return render(request, 'home.html') 

def account_view(request):
    # Your account view logic
    return render(request, 'account.html')

def orders_view(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'orders.html', {'orders': orders})

def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.status = 'Cancelled'
    order.save()
    messages.success(request, 'Your order has been cancelled.')
    return redirect('orders_view')
def logout_view(request):
    logout(request)
    return redirect('index')  # Redirect to home or another page after logout

def admin_home(request):
    return render(request, 'admin_home.html')

def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

def admin_categories(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Category.objects.create(name=name)
            return redirect('admin_categories')
    categories = Category.objects.all()
    return render(request, 'admin_categories.html', {'categories': categories})
    # return render(request, 'admin_categories.html')

def admin_products(request):
    products = Product.objects.all()
    return render(request, 'admin_products.html', {'products': products})
    # return render(request, 'admin_products.html')

def admin_users(request):
    return render(request, 'admin_users.html')

def admin_update_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            category.name = name
            category.save()
            return redirect('admin_categories')
    return render(request, 'admin_update_category.html', {'category': category})

def admin_delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        return redirect('admin_categories')
    return render(request, 'admin_delete_category.html', {'category': category})

def admin_add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.save()
            return redirect('admin_products')  # Replace 'product_list' with your product list view name
    else:
        form = ProductForm()
    return render(request, 'admin_add_product.html', {'form': form})

def product_list(request):
    products = Product.objects.all()
    return render(request, 'admin_products.html', {'products': products})

def admin_update_product(request, pk):
    product = get_object_or_404(Product, pk=pk)    
    if request.method == 'POST':
        product.name = request.POST.get('name')        
        # Handle category
        category_id = request.POST.get('category')
        if category_id:
            product.category = get_object_or_404(Category, id=category_id)        
        product.price = request.POST.get('price')
        product.description = request.POST.get('description')
        # Handle images
        for i in range(1, 6):  # Corrected range to 6 (from 1 to 5)
            image_field = f'image{i}'
            if image_field in request.FILES:
                setattr(product, image_field, request.FILES[image_field])
        product.save()
        return redirect('admin_products')    
    categories = Category.objects.all()
    return render(request, 'admin_update_product.html', {'product': product, 'categories': categories})

def admin_delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)    
    if request.method == 'POST':
        # Confirming the deletion
        product.delete()
        return redirect('admin_products')  # Redirect to a list view or another appropriate page    
    return render(request, 'admin_delete_product.html', {'product': product})