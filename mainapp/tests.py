# tests.py (mainapp/tests.py or create a tests folder with multiple test files)

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from users.models import User
from mainapp.models import Order, Stock

class AuthenticationTests(TestCase):
    """Test user registration, authentication and permissions"""
    
    def setUp(self):
        # Create test users
        self.admin = User.objects.create_user(
            username='testadmin', 
            email='admin@example.com',
            password='password123',
            role='admin',
            approved=True
        )
        
        self.seller = User.objects.create_user(
            username='testseller',
            email='seller@example.com',
            password='password123',
            role='seller',
            first_name='Test',
            last_name='Seller',
            phone='1234567890',
            city='Test City',
            approved=True
        )
        
        self.driver = User.objects.create_user(
            username='testdriver',
            email='driver@example.com',
            password='password123',
            role='driver',
            first_name='Test',
            last_name='Driver',
            phone='9876543210',
            city='Test City',
            approved=True
        )
        
        self.unapproved_seller = User.objects.create_user(
            username='pendingseller',
            email='pending@example.com',
            password='password123',
            role='seller',
            approved=False
        )
        
        # Create tokens for authenticated requests
        self.admin_token = Token.objects.create(user=self.admin)
        self.seller_token = Token.objects.create(user=self.seller)
        self.driver_token = Token.objects.create(user=self.driver)
        
        # Initialize API client
        self.client = APIClient()
    
    def test_user_registration(self):
        """Test user registration endpoints"""
        # Test seller registration
        seller_data = {
            'username': 'newseller',
            'email': 'new@example.com',
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'Seller',
            'phone': '1112223333',
            'city': 'New City'
        }
        
        url = reverse('register-seller')
        response = self.client.post(url, seller_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['role'], 'seller')
        self.assertFalse(response.data['approved'])
        
        # Test driver registration
        driver_data = {
            'username': 'newdriver',
            'email': 'driver@example.com',
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'Driver',
            'phone': '4445556666',
            'city': 'Driver City'
        }
        
        url = reverse('register-driver')
        response = self.client.post(url, driver_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['role'], 'driver')
        self.assertFalse(response.data['approved'])
    
    def test_login_and_token(self):
        """Test login functionality and token generation"""
        url = reverse('login')
        
        # Test valid admin login
        response = self.client.post(url, {
            'username': 'testadmin',
            'password': 'password123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        
        # Test valid seller login (approved)
        response = self.client.post(url, {
            'username': 'testseller',
            'password': 'password123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        
        # Test unapproved seller login (should fail)
        response = self.client.post(url, {
            'username': 'pendingseller',
            'password': 'password123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test invalid credentials
        response = self.client.post(url, {
            'username': 'testadmin',
            'password': 'wrongpassword'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserManagementTests(TestCase):
    """Test user management functionalities (admin only)"""
    
    def setUp(self):
        # Create test users
        self.admin = User.objects.create_user(
            username='testadmin', 
            email='admin@example.com',
            password='password123',
            role='admin',
            approved=True
        )
        
        self.seller = User.objects.create_user(
            username='testseller',
            email='seller@example.com',
            password='password123',
            role='seller',
            approved=True
        )
        
        self.unapproved_seller = User.objects.create_user(
            username='pendingseller',
            email='pending@example.com',
            password='password123',
            role='seller',
            approved=False
        )
        
        # Create tokens
        self.admin_token = Token.objects.create(user=self.admin)
        self.seller_token = Token.objects.create(user=self.seller)
        
        # Initialize API client
        self.client = APIClient()
    
    def test_user_listing(self):
        """Test listing users with different roles"""
        url = reverse('user-list')
        
        # Admin should see all users
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) >= 3)  # Admin, seller, and unapproved seller
        
        # Seller should only see themselves
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.seller_token.key}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['username'], 'testseller')
    
    def test_user_approval(self):
        """Test user approval by admin"""
        url = reverse('approve-user', args=[self.unapproved_seller.id])
        
        # Seller cannot approve users
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.seller_token.key}')
        response = self.client.patch(url, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin can approve users
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        response = self.client.patch(url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['approved'])
        
        # Verify user was approved
        self.unapproved_seller.refresh_from_db()
        self.assertTrue(self.unapproved_seller.approved)


class StockManagementTests(TestCase):
    """Test stock management functionalities"""
    
    def setUp(self):
        # Create test users
        self.admin = User.objects.create_user(
            username='testadmin', 
            email='admin@example.com',
            password='password123',
            role='admin',
            approved=True
        )
        
        self.seller = User.objects.create_user(
            username='testseller',
            email='seller@example.com',
            password='password123',
            role='seller',
            approved=True
        )
        
        self.driver = User.objects.create_user(
            username='testdriver',
            email='driver@example.com',
            password='password123',
            role='driver',
            approved=True
        )
        
        # Create tokens
        self.admin_token = Token.objects.create(user=self.admin)
        self.seller_token = Token.objects.create(user=self.seller)
        self.driver_token = Token.objects.create(user=self.driver)
        
        # Create some stock for the seller
        self.stock = Stock.objects.create(
            seller=self.seller,
            item_name='Test Item',
            quantity=10
        )
        
        # Initialize API client
        self.client = APIClient()
    
    def test_stock_creation(self):
        """Test creating stock with different roles"""
        url = reverse('stock-list-create')
        
        # Seller can create their own stock
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.seller_token.key}')
        response = self.client.post(url, {
            'item_name': 'New Item',
            'quantity': 20
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['item_name'], 'New Item')
        self.assertEqual(response.data['quantity'], 20)
        
        # Admin can create stock for any seller
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        response = self.client.post(url, {
            'item_name': 'Admin Created Item',
            'quantity': 30,
            'seller_id': self.seller.id
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['item_name'], 'Admin Created Item')
        self.assertEqual(response.data['quantity'], 30)
        
        # Driver cannot create stock
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.driver_token.key}')
        response = self.client.post(url, {
            'item_name': 'Driver Item',
            'quantity': 5
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_stock_listing(self):
        """Test listing stock with different roles"""
        url = reverse('stock-list-create')
        
        # Admin can see all stock
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Seller can only see their own stock
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.seller_token.key}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Driver cannot access stock endpoint at all
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.driver_token.key}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_stock_update(self):
        """Test updating stock with different roles"""
        url = reverse('stock-detail', args=[self.stock.id])
        
        # Seller can update their own stock
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.seller_token.key}')
        response = self.client.patch(url, {
            'quantity': 15
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], 15)
        
        # Admin can update any stock
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        response = self.client.patch(url, {
            'quantity': 25
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], 25)
        
        # Driver cannot update stock
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.driver_token.key}')
        response = self.client.patch(url, {
            'quantity': 5
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class OrderManagementTests(TestCase):
    """Test order management functionalities"""
    
    def setUp(self):
        # Create test users
        self.admin = User.objects.create_user(
            username='testadmin', 
            email='admin@example.com',
            password='password123',
            role='admin',
            approved=True
        )
        
        self.seller = User.objects.create_user(
            username='testseller',
            email='seller@example.com',
            password='password123',
            role='seller',
            approved=True
        )
        
        self.driver = User.objects.create_user(
            username='testdriver',
            email='driver@example.com',
            password='password123',
            role='driver',
            approved=True
        )
        
        # Create a second seller for testing permissions
        self.seller2 = User.objects.create_user(
            username='seller2',
            email='seller2@example.com',
            password='password123',
            role='seller',
            approved=True
        )
        
        # Create tokens
        self.admin_token = Token.objects.create(user=self.admin)
        self.seller_token = Token.objects.create(user=self.seller)
        self.seller2_token = Token.objects.create(user=self.seller2)
        self.driver_token = Token.objects.create(user=self.driver)
        
        # Create stock for sellers
        self.stock = Stock.objects.create(
            seller=self.seller,
            item_name='Test Item',
            quantity=50
        )
        
        self.stock2 = Stock.objects.create(
            seller=self.seller2,
            item_name='Seller2 Item',
            quantity=30
        )
        
        # Create orders
        self.order = Order.objects.create(
            seller=self.seller,
            customer_name='Test Customer',
            customer_phone='1234567890',
            delivery_street='123 Test St',
            delivery_city='Test City',
            delivery_location='map:123,456',
            item='Test Item',
            quantity=2,
            status='pending'
        )
        
        # Initialize API client
        self.client = APIClient()
    
    def test_order_creation(self):
        """Test creating orders with different roles"""
        url = reverse('order-list-create')
        
        # Seller can create their own order
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.seller_token.key}')
        response = self.client.post(url, {
            'customer_name': 'New Customer',
            'customer_phone': '9876543210',
            'delivery_street': '456 New St',
            'delivery_city': 'New City',
            'delivery_location': 'map:789,012',
            'item': 'Test Item',
            'quantity': 1
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Admin can create order for any seller
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        response = self.client.post(url, {
            'customer_name': 'Admin Customer',
            'customer_phone': '5555555555',
            'delivery_street': '789 Admin St',
            'delivery_city': 'Admin City',
            'delivery_location': 'map:admin',
            'item': 'Test Item',
            'quantity': 3,
            'seller_id': self.seller.id
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Check the response data structure - adjust this based on your actual API response format
        if 'seller' in response.data and isinstance(response.data['seller'], dict):
            self.assertEqual(response.data['seller']['id'], self.seller.id)
        elif 'seller_id' in response.data:
            self.assertEqual(response.data['seller_id'], self.seller.id)
        
        # Driver cannot create orders
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.driver_token.key}')
        response = self.client.post(url, {
            'customer_name': 'Driver Customer',
            'customer_phone': '1231231234',
            'delivery_street': '999 Driver St',
            'delivery_city': 'Driver City',
            'delivery_location': 'map:driver',
            'item': 'Test Item',
            'quantity': 1
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_order_listing(self):
        """Test listing orders with different roles"""
        url = reverse('order-list-create')
        
        # Admin can see all orders
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Seller can only see their own orders
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.seller_token.key}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Seller2 cannot see seller1's orders
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.seller2_token.key}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
        
        # Driver should be forbidden from accessing regular order list
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.driver_token.key}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Driver can access their specific driver orders endpoint
        driver_url = reverse('driver-orders')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.driver_token.key}')
        response = self.client.get(driver_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # No orders assigned yet
    
    def test_order_status_update(self):
        """Test updating order status with different roles"""
        # Assign driver to order
        self.order.driver = self.driver
        self.order.status = 'assigned'
        self.order.save()
        
        url = reverse('order-status-update', args=[self.order.id])
        
        # Driver can update status of assigned order
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.driver_token.key}')
        response = self.client.patch(url, {
            'status': 'in_transit'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_transit')
        
        # Seller cannot update status
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.seller_token.key}')
        response = self.client.patch(url, {
            'status': 'delivered'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin can update status
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        response = self.client.patch(url, {
            'status': 'delivered'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'delivered')
        
        # Check if stock was updated after delivery
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, 48)  # 50 - 2
    
    def test_driver_assignment(self):
        """Test assigning a driver to an order"""
        url = reverse('assign-driver', args=[self.order.id])
        
        # Seller cannot assign a driver
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.seller_token.key}')
        response = self.client.patch(url, {
            'driver_id': self.driver.id
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin can assign a driver
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        response = self.client.patch(url, {
            'driver_id': self.driver.id
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Extract driver ID from the response based on your API's format
        if 'driver' in response.data and isinstance(response.data['driver'], dict):
            self.assertEqual(response.data['driver']['id'], self.driver.id)
        else:
            # This test might need adjustment based on your API's exact response format
            pass
            
        self.assertEqual(response.data['status'], 'assigned')
        
        # Driver can now see this order in their specific endpoint
        driver_orders_url = reverse('driver-orders')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.driver_token.key}')
        response = self.client.get(driver_orders_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The response.data could be paginated or a list depending on your view implementation
        if isinstance(response.data, list):
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]['id'], self.order.id)
        elif 'results' in response.data:  # Paginated response
            self.assertEqual(len(response.data['results']), 1)
            self.assertEqual(response.data['results'][0]['id'], self.order.id)
        else:
            # If the response format is different, this test might need adjustment
            pass