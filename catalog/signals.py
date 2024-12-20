from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Product, Category


# Очистка кеша после сохранения или удаления продукта
@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def clear_products_cache(sender, instance, **kwargs):
    cache.delete('products_list')  # Очистка кеша продуктов


# Очистка кеша после сохранения или удаления категории
@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def clear_categories_cache(sender, instance, **kwargs):
    cache.delete('categories_list')  # Очистка кеша категорий
