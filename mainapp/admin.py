from django.contrib import admin
from .models import  Order, Stock



@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'seller', 'driver', 'item', 'quantity', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'customer_phone', 'item', 'delivery_street', 'delivery_city')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('seller', 'driver')  

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller', 'item_name', 'quantity')
    list_filter = ('seller',)
    search_fields = ('item_name',)