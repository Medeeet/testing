from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from shop.models import Product, Category, Cart, CartItem, Order

class CartViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            name="Laptop",
            slug="laptop",
            category=self.category,
            price=1000,
            available=True
        )
        self.user = User.objects.create_user(username="testuser", password="12345")

    def test_get_or_create_cart_anonymous(self):
        response = self.client.get(reverse("shop:cart_detail"))
        self.assertEqual(response.status_code, 200)
        cart = Cart.objects.first()
        self.assertIsNotNone(cart)
        self.assertIsNotNone(cart.session_key)

    def test_cart_add(self):
        url = reverse("shop:cart_add", args=[self.product.id])
        response = self.client.post(url, {"quantity": 2})
        self.assertRedirects(response, reverse("shop:cart_detail"))
        cart = Cart.objects.first()
        item = CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(item.quantity, 2)

    def test_cart_remove(self):
        session = self.client.session
        session.save()
        session_key = session.session_key
        cart = Cart.objects.create(session_key=session_key)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1, price=self.product.price)
        url = reverse("shop:cart_remove", args=[self.product.id])
        response = self.client.get(url)
        self.assertRedirects(response, reverse("shop:cart_detail"))
        self.assertFalse(CartItem.objects.filter(cart=cart, product=self.product).exists())

    def test_cart_detail(self):
        url = reverse("shop:cart_detail")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "shop/cart/detail.html")

    def test_order_create_authenticated(self):
        self.client.login(username="testuser", password="12345")
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1, price=self.product.price)

        url = reverse("shop:order_create")
        response = self.client.post(url, {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "address": "123 Street",
            "postal_code": "12345",
            "city": "Almaty"
        })
        self.assertEqual(response.status_code, 302)  # redirect to order_detail
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.items.count(), 1)
        self.assertFalse(cart.items.exists())
