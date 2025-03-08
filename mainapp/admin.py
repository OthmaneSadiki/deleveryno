from django.contrib import admin
from .models import Address, Order, Stock

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'street', 'city')
    search_fields = ('street', 'city')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'seller', 'driver', 'item', 'quantity', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'customer_phone', 'item')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('seller', 'driver', 'delivery_address')


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller', 'item_name', 'quantity')
    list_filter = ('seller',)
    search_fields = ('item_name',)