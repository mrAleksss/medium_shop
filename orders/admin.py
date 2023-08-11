from django.contrib import admin
from .models import Payment, Order, OrderProduct
from django.db.models import Sum
from django.shortcuts import redirect


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    readonly_fields = ('payment', 'user', 'product', 'quantity', 'product_price', 'ordered')
    extra = 0


class OrderPaymentInline(admin.TabularInline):
    model = Payment
    readonly_fields = ('amount_paid',)
    extra = 0




class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'phone', 'email', 'city', 'order_total', 'remaining_balance', 'status', 'is_ordered', 'created_at']
    list_filter = ['status', 'is_ordered']
    search_fields = ['order_number', 'first_name', 'last_name', 'phone', 'email']
    list_per_page = 10
    # actions = ['update_remaining_balance']
    inlines = [OrderProductInline, OrderPaymentInline]

    # def update_remaining_balance(self, request, queryset):
    #     for order in queryset:
    #         payments = Payment.objects.filter(order=order)
    #         total_amount_paid = payments.aggregate(total_amount=Sum('amount_paid'))['total_amount']
    #         order.remaining_balance = order.order_total - total_amount_paid
    #         order.save()

    #     self.message_user(request, "Remaining balance updated successfully.")
    #     return redirect('admin:app_label_order_changelist')


admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(OrderProduct)
