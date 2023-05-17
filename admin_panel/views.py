from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import auth,messages
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from .models import Product
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

# Create your views here.

@never_cache
@login_required(login_url='login')
def home(request):
    product=Product.objects.all()
    context={
        'products':product
    }
    return render(request,'home.html',context)

@never_cache
def login(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method=='POST':
            username=request.POST['username']
            password=request.POST['password']
            user=auth.authenticate(request,username=username,password=password)
            if user is not None:
                auth.login(request,user)
                return redirect('home')
            else:
                messages.error(request,'invalid password or username')
            
                
        return render(request,'login.html')

@never_cache
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = User.objects.create_user(username=username, password=password)
        user.save()

        return redirect('login')
    else:
        return render(request, 'registration.html')
    
def logout(request):
    auth.logout(request)
    return redirect('login')

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    current_user = request.user
    product = get_object_or_404(Product, id=product_id) 

    if current_user.is_authenticated:
        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()

        if is_cart_item_exists:
            cart_item = CartItem.objects.get(product=product, user=current_user)
            cart_item.quantity += 1
            cart_item.save()
        else:
            cart_item = CartItem.objects.create(product=product, quantity=1, user=current_user)
        return redirect('cart')
    else:
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()

        if is_cart_item_exists:
            cart_item = CartItem.objects.get(product=product, cart=cart)
            cart_item.quantity += 1
            cart_item.save()
        else:
            cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
        return redirect('cart')

def remove_cart(request, product_id, cart_item_id):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        product = get_object_or_404(Product, id=product_id)
        try:
            if request.user.is_authenticated:
                cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
            else:
                cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
            
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
        except CartItem.DoesNotExist:
            return redirect('cart')
    except Cart.DoesNotExist:
        return redirect('cart')
    
    return redirect('cart')


def remove_cart_item(request,product_id,cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart= Cart.objects.get(cart_id = _cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')

def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0 
        grand_total = 0    
        if request.user.is_authenticated:
            cart_items = CartItem.objects.all()
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        grand_total = total 
    except ObjectDoesNotExist:
        pass 
    
    context = {
        'total':total,
        'quantity':quantity,
        'cart_items':cart_items,
        'grand_total':grand_total,
    }
    return render(request,'cart.html',context)

def product_details(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e
    context = { 
        'single_product': single_product,
        'in_cart':in_cart,
    }
    return render(request, '', context)