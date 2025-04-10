from datetime import timezone
from django.db import models

from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('seller', 'Seller'),
        ('driver', 'Driver'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    approved = models.BooleanField(default=False)
    email = models.EmailField(unique=True)
    rib = models.CharField(max_length=100, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-updated_at', '-date_joined']  # Order by updated_at first, then date_joined
        indexes = [
            models.Index(fields=['-updated_at']),
            models.Index(fields=['-date_joined']),
            models.Index(fields=['role']),
            models.Index(fields=['approved']),
        ]
    
    def save(self, *args, **kwargs):
        # Set updated_at on first save if not already set
        if not self.pk and not self.updated_at:
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)
