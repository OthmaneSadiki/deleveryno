from django.db import models
from django.conf import settings


class Address(models.Model):
    """
    Represents a physical address used for order delivery.
    """
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    
    
    def __str__(self):
        return f"{self.street}, {self.city}"


class Order(models.Model):
    """
    Represents an order created by a seller.
    - A seller creates an order with customer details, delivery address, and item information.
    - Only admins can assign a driver to the order by updating the `driver` field.
    - Once a driver is assigned, only that driver (or an admin) should update the order's status.
    """
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Driver Assigned'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
        ('no_answer', 'No Answer'),
        ('postponed', 'Postponed'),
    ]

    # The seller who created the order.
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )
    # Customer details provided by the seller.
    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=20)
    # Delivery address for the order.
    delivery_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders"
    )
    # Item details.
    item = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    # Order status: the lifecycle from order creation through delivery.
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='pending'
    )
    # The driver assigned to deliver the order; initially null.
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_orders"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.pk} by {self.seller}"


class Stock(models.Model):
    """
    Represents a seller's inventory of items.
    The stock quantity is automatically decremented when an order is completed.
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

