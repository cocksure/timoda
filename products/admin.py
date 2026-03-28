from django.contrib import admin
from django.core.cache import cache
from .models import Category, Size, Color, Product, ProductImage, ProductVariant, Review, Favorite


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'order']
    list_filter = ['is_active', 'parent']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'order']


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    list_editable = ['order']


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'hex_code']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ['image', 'alt_text', 'is_primary', 'order']


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 3
    fields = ['size', 'color', 'stock', 'sku']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'section', 'price', 'sale_price', 'is_featured', 'is_new', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_featured', 'is_new', 'section', 'category']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['section', 'is_featured', 'is_new', 'is_active']
    inlines = [ProductImageInline, ProductVariantInline]
    fieldsets = (
        ('Основное', {'fields': ('category', 'section', 'name', 'slug', 'description', 'composition', 'care_instructions')}),
        ('Цены', {'fields': ('price', 'sale_price')}),
        ('Настройки', {'fields': ('is_featured', 'is_new', 'is_active')}),
        ('SEO', {'fields': ('meta_title', 'meta_description'), 'classes': ('collapse',)}),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating']
    list_editable = ['is_approved']
    search_fields = ['product__name', 'user__email', 'comment']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cache.delete(f'product_detail_{obj.product.slug}')

    def delete_model(self, request, obj):
        slug = obj.product.slug
        super().delete_model(request, obj)
        cache.delete(f'product_detail_{slug}')

    def delete_queryset(self, request, queryset):
        slugs = set(queryset.values_list('product__slug', flat=True))
        super().delete_queryset(request, queryset)
        for slug in slugs:
            cache.delete(f'product_detail_{slug}')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'product__name']