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
from django.utils.timezone import now
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
import random
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from django.db.models import Sum
import urllib, base64
import io
from django.db.models.functions import TruncMonth


# Create your views here.

User = get_user_model()

@login_required
def index(request):
    products = list(Product.objects.all())
    random_products = random.sample(products, min(len(products), 10))
    return render(request, 'index.html', {'random_products': random_products})

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
    paginator = Paginator(products, 12)  # 15 products per page
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

            # Create an Order
            order = Order.objects.create(user=request.user, order_date=now(), status='Pending')
            
            # Create OrderItems
            for item in cart_items:
                OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)
            
            # Clear the cart
            cart_items.delete()
            cart.delete()

            # Determine payment method chosen
            payment_method = form.cleaned_data['payment_method']
            if payment_method == 'Cash On Delivery':
                messages.success(request, 'Your order has been placed successfully!')
                return redirect('orders')
            elif payment_method == 'Prepaid':
                messages.info(request, 'Redirecting to payment gateway...')
                return redirect('payment_gateway')  # Replace with actual URL
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
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'orders.html', {'orders': orders})

@login_required
def view_order_details(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    order_items = order.items.all()  # Assuming you have a related_name='items' in OrderItem model
    return render(request, 'order_details.html', {'order': order, 'order_items': order_items})

@login_required
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if order.status == 'Pending':
        order.status = 'Cancelled'
        order.save()
        messages.success(request, 'Your order has been cancelled.')
    else:
        messages.error(request, 'You cannot cancel this order.')
    return redirect('orders')

def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)

    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{order_id}.pdf"'

    # Create the PDF object, using the response object as its "file."
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Draw the order details
    p.drawString(100, height - 100, f"Order ID: {order.id}")
    p.drawString(100, height - 120, f"Order Date: {order.order_date}")
    p.drawString(100, height - 140, f"Status: {order.status}")

    # Draw the table header
    p.drawString(100, height - 180, "Product Name")
    p.drawString(300, height - 180, "Quantity")
    p.drawString(400, height - 180, "Price")

    # Draw the order items
    y = height - 200
    for item in order_items:
        p.drawString(100, y, item.product.name)
        p.drawString(300, y, str(item.quantity))
        p.drawString(400, y, str(item.product.price))
        y -= 20

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()

    return response


def logout_view(request):
    logout(request)
    return redirect('index')  # Redirect to home or another page after logout

def admin_home(request):
    return render(request, 'admin_home.html')

def admin_dashboard(request):
    # Fetch category-wise sales data
    category_sales = (
        OrderItem.objects
        .values('product__category__name')
        .annotate(total_sales=Sum('quantity'))
    )
    
    labels = [cs['product__category__name'] for cs in category_sales]
    sizes = [cs['total_sales'] for cs in category_sales]
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#c2c2f0', '#ffb3e6']
    
    # Dynamically generate explode list
    explode = [0] * len(sizes)
    if sizes:
        explode[0] = 0.1  # explode 1st slice if there is at least one size

    # Generate pie chart
    fig, ax = plt.subplots()
    ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
           shadow=True, startangle=140)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    # Save the pie chart to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    pie_string = base64.b64encode(buf.read())
    pie_uri = urllib.parse.quote(pie_string)
    plt.close()

    # Fetch monthly sales data
    monthly_sales = (
        OrderItem.objects
        .annotate(month=TruncMonth('order__order_date'))
        .values('month')
        .annotate(total_sales=Sum('quantity'))
        .order_by('month')
    )

    months = [ms['month'].strftime('%B %Y') for ms in monthly_sales]
    sales = [ms['total_sales'] for ms in monthly_sales]

    # Generate bar chart
    fig, ax = plt.subplots()
    ax.bar(months, sales, color='#66b3ff')

    ax.set_xlabel('Month')
    ax.set_ylabel('Total Sales')
    ax.set_title('Monthly Sales')

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Save the bar chart to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    bar_string = base64.b64encode(buf.read())
    bar_uri = urllib.parse.quote(bar_string)
    plt.close()

    return render(request, 'admin_dashboard.html', {'pie_data': pie_uri, 'bar_data': bar_uri})

def admin_orders(request):
    orders = Order.objects.all().order_by('-order_date')
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        status = request.POST.get('status')
        order = get_object_or_404(Order, id=order_id)
        order.status = status
        order.save()
        return redirect('admin_orders')
    return render(request, 'admin_orders.html', {'orders': orders})

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


def admin_orders_by_status(request, status):
    orders = Order.objects.filter(status=status)
    return render(request, 'admin_orders_by_status.html', {'orders': orders, 'status': status})

def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        status = request.POST.get('status')
        order.status = status
        order.save()
        return redirect('admin_orders_by_status', status=order.status)
    return render(request, 'update_order_status.html', {'order_id': order_id})