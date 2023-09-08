from django.contrib import admin
from .models import Product, Variation, ReviewRating, ProductGallery, PriceTier, Rate_to_uah, BicycleCharacteristics
import admin_thumbnails


@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1


class PriceTierInline(admin.TabularInline):
    model = PriceTier


class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'price', 'price_in_uah', 'stock', 'category', 'modified_date', 'is_available')
    prepopulated_fields = {"slug": ("product_name", )}
    inlines = [PriceTierInline, ProductGalleryInline]

class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active',)
    list_editable = ('is_active',)
    list_filter = ('product', 'variation_category', 'variation_value')

class PriceTierAdmin(admin.ModelAdmin):
    list_display = ('product', 'min_quantity', 'discount')


admin.site.register(Product, ProductAdmin)
admin.site.register(Variation, VariationAdmin)
admin.site.register(BicycleCharacteristics)
admin.site.register(ReviewRating)
admin.site.register(ProductGallery)
admin.site.register(Rate_to_uah)
admin.site.register(PriceTier, PriceTierAdmin)