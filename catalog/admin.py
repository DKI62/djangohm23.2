from django.contrib import admin
from django.core.exceptions import PermissionDenied
from .models import Category, Product, BlogPost, Version


# Настройка для модели Category
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


# Настройка для модели Product
class VersionInline(admin.TabularInline):
    model = Version
    extra = 1  # Количество пустых форм для добавления новых версий (по умолчанию 1)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [VersionInline]
    list_display = ('id', 'name', 'price', 'category', 'get_active_version')
    list_filter = ('category',)
    search_fields = ('name', 'description')

    def get_active_version(self, obj):
        """Получение активной версии продукта."""
        active_version = obj.versions.filter(is_active=True).first()
        return active_version.version_name if active_version else 'No active version'

    get_active_version.short_description = 'Active Version'

    # Ограничение прав на редактирование полей
    def save_model(self, request, obj, form, change):
        """Проверка прав на изменение полей."""
        if 'description' in form.changed_data and not request.user.has_perm('catalog.can_edit_product_description'):
            raise PermissionDenied("You do not have permission to edit the product description.")

        if 'category' in form.changed_data and not request.user.has_perm('catalog.can_change_product_category'):
            raise PermissionDenied("You do not have permission to change the product category.")

        if 'publish_status' in form.changed_data and not request.user.has_perm('catalog.can_unpublish_product'):
            raise PermissionDenied("You do not have permission to change the publish status.")

        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        """Делаем поле publish_status доступным только для чтения, если нет прав."""
        if not request.user.has_perm('catalog.can_unpublish_product'):
            return ['publish_status']
        return []

    # Экшен для снятия продуктов с публикации
    @admin.action(description="Unpublish selected products")
    def unpublish_products(self, request, queryset):
        if not request.user.has_perm('catalog.can_unpublish_product'):
            raise PermissionDenied("You do not have permission to unpublish products.")
        queryset.update(publish_status='unpublished')

    actions = ['unpublish_products']  # Регистрация экшена


# Настройка для модели BlogPost
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'created_at', 'is_published', 'views_count']
    list_filter = ['is_published', 'created_at']
    search_fields = ['title', 'content']


class VersionAdmin(admin.ModelAdmin):
    list_display = ('product', 'version_number', 'version_name', 'is_active')
    list_filter = ('is_active', 'product')


admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(Version, VersionAdmin)
