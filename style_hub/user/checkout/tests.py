from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from admin_panel.couponmanagement.models import Coupon
from admin_panel.categorymanagement.models import Category
from admin_panel.productmanagement.models import Product, ProductVariant, Offer
from user.cart.models import Cart
from user.orders.models import Order, OrderItem
from user.addresses.models import Address

User = get_user_model()

class CheckoutCouponOfferTests(TestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password123',
            is_active=True
        )
        
        # Setup Address
        self.address = Address.objects.create(
            user=self.user,
            full_name='Test User',
            phone_number='1234567890',
            house_name='Test House',
            address='Test Street',
            area='Test Area',
            district='Test District',
            state='Test State',
            country='Test Country',
            pincode='123456',
            is_default=True
        )

        # Setup Category
        self.category = Category.objects.create(
            category_name='Clothing',
            description='Mens Clothing',
            is_active=True,
            is_deleted=False
        )

        # Setup Product
        self.product = Product.objects.create(
            category=self.category,
            product_name='Tailored Shirt',
            description='Premium tailored shirt',
            is_active=True,
            is_deleted=False
        )

        # Setup ProductVariant
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size='M',
            color='White',
            variant_price=Decimal('100.00'),
            variant_stock=10,
            is_active=True,
            is_deleted=False
        )

        # Client and login
        self.client = Client()
        self.client.login(username='testuser', password='password123')
        
        self.today = timezone.now().date()

    def test_fixed_coupon(self):
        """Test a fixed amount coupon applies correctly."""
        coupon = Coupon.objects.create(
            code='FIXED20',
            title='Flat 20 Off',
            discount_type='FIXED',
            discount_value=Decimal('20.00'),
            min_purchase=Decimal('50.00'),
            max_discount=Decimal('0.00'),
            start_date=self.today,
            end_date=self.today + timedelta(days=5),
            usage_limit_per_user=1,
            is_active=True
        )

        # Add item to cart
        Cart.objects.create(user=self.user, variant=self.variant, quantity=1)

        # Apply Coupon
        response = self.client.post('/checkout/apply-coupon/', {'coupon_code': 'FIXED20'}, follow=True)
        self.assertEqual(self.client.session.get('coupon_id'), coupon.id)
        self.assertEqual(Decimal(str(self.client.session.get('discount_amount'))), Decimal('20.00'))

    def test_percentage_coupon(self):
        """Test a percentage discount coupon applies correctly."""
        coupon = Coupon.objects.create(
            code='PERCENT15',
            title='15% Off',
            discount_type='PERCENTAGE',
            discount_value=Decimal('15.00'),
            min_purchase=Decimal('50.00'),
            max_discount=Decimal('50.00'),
            start_date=self.today,
            end_date=self.today + timedelta(days=5),
            usage_limit_per_user=1,
            is_active=True
        )

        # Add item to cart
        Cart.objects.create(user=self.user, variant=self.variant, quantity=1)

        # Apply Coupon
        response = self.client.post('/checkout/apply-coupon/', {'coupon_code': 'PERCENT15'}, follow=True)
        self.assertEqual(self.client.session.get('coupon_id'), coupon.id)
        self.assertEqual(Decimal(str(self.client.session.get('discount_amount'))), Decimal('15.00'))

    def test_expired_coupon(self):
        """Test an expired coupon is blocked from being applied."""
        coupon = Coupon.objects.create(
            code='EXPIRED',
            title='Expired Coupon',
            discount_type='FIXED',
            discount_value=Decimal('20.00'),
            min_purchase=Decimal('50.00'),
            start_date=self.today - timedelta(days=10),
            end_date=self.today - timedelta(days=2),
            usage_limit_per_user=1,
            is_active=True
        )

        # Add item to cart
        Cart.objects.create(user=self.user, variant=self.variant, quantity=1)

        # Apply Coupon
        response = self.client.post('/checkout/apply-coupon/', {'coupon_code': 'EXPIRED'}, follow=True)
        self.assertIsNone(self.client.session.get('coupon_id'))

    def test_minimum_purchase_failed(self):
        """Test coupon application fails if min purchase condition is not met."""
        coupon = Coupon.objects.create(
            code='MIN200',
            title='High Min Purchase',
            discount_type='FIXED',
            discount_value=Decimal('20.00'),
            min_purchase=Decimal('200.00'),
            start_date=self.today,
            end_date=self.today + timedelta(days=5),
            usage_limit_per_user=1,
            is_active=True
        )

        # Add item to cart (worth 100.00)
        Cart.objects.create(user=self.user, variant=self.variant, quantity=1)

        # Apply Coupon
        response = self.client.post('/checkout/apply-coupon/', {'coupon_code': 'MIN200'}, follow=True)
        self.assertIsNone(self.client.session.get('coupon_id'))

    def test_multiple_coupon_apply_blocked(self):
        """Test applying a second coupon is blocked when one is already applied."""
        coupon1 = Coupon.objects.create(
            code='COUPON1',
            title='Coupon 1',
            discount_type='FIXED',
            discount_value=Decimal('10.00'),
            min_purchase=Decimal('10.00'),
            start_date=self.today,
            end_date=self.today + timedelta(days=5),
            usage_limit_per_user=1,
            is_active=True
        )
        coupon2 = Coupon.objects.create(
            code='COUPON2',
            title='Coupon 2',
            discount_type='FIXED',
            discount_value=Decimal('15.00'),
            min_purchase=Decimal('10.00'),
            start_date=self.today,
            end_date=self.today + timedelta(days=5),
            usage_limit_per_user=1,
            is_active=True
        )

        Cart.objects.create(user=self.user, variant=self.variant, quantity=1)

        # Apply Coupon 1
        self.client.post('/checkout/apply-coupon/', {'coupon_code': 'COUPON1'}, follow=True)
        self.assertEqual(self.client.session.get('coupon_id'), coupon1.id)

        # Try to apply Coupon 2
        response = self.client.post('/checkout/apply-coupon/', {'coupon_code': 'COUPON2'}, follow=True)
        # Verify first one is still applied, and second is ignored
        self.assertEqual(self.client.session.get('coupon_id'), coupon1.id)

    def test_product_offer_only(self):
        """Test that a product-specific offer applies correctly."""
        Offer.objects.create(
            name='20% Product Offer',
            discount_type='PERCENTAGE',
            discount_value=Decimal('20.00'),
            start_date=self.today,
            end_date=self.today + timedelta(days=5),
            product=self.product,
            is_active=True
        )

        self.assertEqual(self.variant.offer_price, Decimal('80.00'))
        self.assertTrue(self.variant.has_active_offer)

    def test_category_offer_only(self):
        """Test that a category-specific offer applies correctly."""
        Offer.objects.create(
            name='₹15 Category Offer',
            discount_type='FIXED',
            discount_value=Decimal('15.00'),
            start_date=self.today,
            end_date=self.today + timedelta(days=5),
            category=self.category,
            is_active=True
        )

        self.assertEqual(self.variant.offer_price, Decimal('85.00'))
        self.assertTrue(self.variant.has_active_offer)

    def test_both_offers_exist_biggest_applies(self):
        """Test that if both product and category offers exist, the biggest discount applies."""
        # 1. Product offer: 20% (₹20 discount)
        product_offer = Offer.objects.create(
            name='20% Product Offer',
            discount_type='PERCENTAGE',
            discount_value=Decimal('20.00'),
            start_date=self.today,
            end_date=self.today + timedelta(days=5),
            product=self.product,
            is_active=True
        )
        # 2. Category offer: ₹15 fixed discount
        category_offer = Offer.objects.create(
            name='₹15 Category Offer',
            discount_type='FIXED',
            discount_value=Decimal('15.00'),
            start_date=self.today,
            end_date=self.today + timedelta(days=5),
            category=self.category,
            is_active=True
        )

        # Biggest discount is the product offer (₹20 vs ₹15)
        self.assertEqual(self.variant.offer_price, Decimal('80.00'))

        # Let's change category offer to ₹25 fixed discount (which will make it the biggest)
        category_offer.discount_value = Decimal('25.00')
        category_offer.save()

        # Biggest discount is now category offer (₹25 vs ₹20)
        self.assertEqual(self.variant.offer_price, Decimal('75.00'))

    def test_checkout_order_amount_correct_and_success_clears_coupon(self):
        """Test that the order totals are correct on checkout, variant stock is reduced, and coupon session is cleared."""
        # Add 10% offer on product
        Offer.objects.create(
            name='10% Product Offer',
            discount_type='PERCENTAGE',
            discount_value=Decimal('10.00'),
            start_date=self.today,
            end_date=self.today + timedelta(days=5),
            product=self.product,
            is_active=True
        )

        # Setup Coupon (Flat ₹10 Off)
        Coupon.objects.create(
            code='SAVE10',
            title='Save 10',
            discount_type='FIXED',
            discount_value=Decimal('10.00'),
            min_purchase=Decimal('50.00'),
            start_date=self.today,
            end_date=self.today + timedelta(days=5),
            usage_limit_per_user=1,
            is_active=True
        )

        # Add item to cart
        Cart.objects.create(user=self.user, variant=self.variant, quantity=1)

        # Apply coupon first
        self.client.post('/checkout/apply-coupon/', {'coupon_code': 'SAVE10'}, follow=True)
        self.assertEqual(Decimal(str(self.client.session.get('discount_amount'))), Decimal('10.00'))

        # Place the order
        response = self.client.post('/checkout/', {
            'address_id': self.address.id,
            'payment_method': 'COD'
        }, follow=True)

        self.assertEqual(response.status_code, 200)

        # Verify Order calculations:
        # Product offer-applied price = 100 - 10% = 90.
        # Subtotal = 90.00. Coupon discount = 10.00.
        # Subtotal 90 is < 500, so delivery charge = 50.00.
        # Total = 90 - 10 + 50 = 130.00.
        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.subtotal, Decimal('90.00'))
        self.assertEqual(order.discount_amount, Decimal('10.00'))
        self.assertEqual(order.delivery_charge, Decimal('50.00'))
        self.assertEqual(order.total_amount, Decimal('130.00'))

        # Verify OrderItem price stores final offer-applied price (90.00)
        order_item = OrderItem.objects.filter(order=order).first()
        self.assertEqual(order_item.price, Decimal('90.00'))

        # Verify variant stock decreased by 1
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.variant_stock, 9)

        # Verify coupon is cleared from session
        self.assertIsNone(self.client.session.get('coupon_id'))
        self.assertIsNone(self.client.session.get('discount_amount'))
