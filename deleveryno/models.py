from django.db import models
from django.conf import settings
from django.utils import timezone

class Address(models.Model):
    """
    Represents a physical address for deliveries.
    This can be used to store the delivery address for orders and deliveries.
    """
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.street}, {self.city}"


class Order(models.Model):
    """
    An order created by a seller (or admin on a seller's behalf) for a delivery.
    It contains the customer's contact information, the delivery address, and a status.
    """
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('done', 'Done'),
        ('canceled', 'Canceled'),
        ('no_answer', 'No Answer'),
        ('postponed', 'Postponed'),
    ]

    # The seller who creates the order.
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )
    # Customer information provided by the seller.
    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=20)
    # Delivery address is stored separately to enable reuse and easier management.
    delivery_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders"
    )
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.pk} by {self.seller} for {self.customer_name}"


class Delivery(models.Model):
    """
    A delivery is created once an order is set to be delivered.
    Only the driver or admin can update its status.
    The admin assigns a driver (based on the city) for each delivery.
    """
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]

    # One-to-one with an order; each order has one delivery record.
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="delivery"
    )
    # The driver assigned by the admin.
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deliveries"
    )
    # Although the order already has a delivery address, this field can allow flexibility.
    delivery_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deliveries"
    )
    # Redundant storage of customer's contact info can be useful in the delivery context.
    customer_full_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=20)
    # Details about the item being delivered.
    item = models.CharField(max_length=255)
    number_of_items = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS_CHOICES,
        default='pending'
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Delivery for Order #{self.order.pk}"


class Stock(models.Model):
    """
    Represents a seller's inventory of items.
    Each seller maintains a stock list (item name and quantity available).
    When an order is completed, you can deduct the ordered quantity from the stock.
    """
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stock_items"
    )
    item_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.item_name} - {self.quantity}"
