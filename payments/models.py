from django.db import models

# Create your models here.
from django.db import models

class Payment(models.Model):
    PAYMENT_STATUS = [
        ('created', 'Created'),
        ('approved', 'Approved'),
        ('failed', 'Failed'),
        ('completed', 'Completed'),
    ]

    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paypal_payment_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='completed')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.amount}"