from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError




class Order(models.Model):
    """
    Represents an order created by a seller.
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

    # The seller who created the order
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )
    
    # Customer details provided by the seller
    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=20)
    
    # Delivery address details (flattened from the previous Address model)
    delivery_street = models.CharField(max_length=255)
    delivery_city = models.CharField(max_length=100)
    delivery_location = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Google Maps location string"
    )
    
    # Item details
    item = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    
    # Order status and assignment
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='pending'
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_orders"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate status transitions"""
        if not self.pk:
            return  # Skip validation for new orders
            
        old_instance = Order.objects.get(pk=self.pk)
        
        # Define valid status transitions
        valid_transitions = {
            'pending': ['assigned', 'canceled'],
            'assigned': ['in_transit', 'canceled', 'pending'],
            'in_transit': ['delivered', 'no_answer', 'postponed', 'canceled'],
            'no_answer': ['in_transit', 'canceled', 'postponed'],
            'postponed': ['in_transit', 'canceled'],
            'delivered': [],  # Terminal state
            'canceled': [],   # Terminal state
        }
        
        if (old_instance.status != self.status and 
            self.status not in valid_transitions.get(old_instance.status, [])):
            raise ValidationError(f"Invalid status transition from {old_instance.status} to {self.status}")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.pk} by {self.seller.username} for {self.customer_name}"
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['seller']),
            models.Index(fields=['driver']),
        ]


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
    approved = models.BooleanField(default=False)  # New field for admin approval
    created_at = models.DateTimeField(auto_now_add=True)  # Track when item was added
    updated_at = models.DateTimeField(auto_now=True)  # Track when item was updated

    def __str__(self):
        return f"{self.item_name} - {self.quantity} - {'Approved' if self.approved else 'Pending'}"


