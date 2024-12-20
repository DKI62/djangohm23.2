import logging

from django.core.cache import cache
from .models import Category, Product

logger = logging.getLogger(__name__)


def get_categories():
    categories = cache.get('categories_list')
    if not categories:
        categories = Category.objects.all()
        cache.set('categories_list', categories, timeout=60 * 15)
        logger.info("Categories fetched from DB and cached.")
    else:
        logger.info("Categories fetched from cache.")
    return categories


def get_products():
    products = cache.get('products_list')
    if not products:
        logger.info("Fetching products from the database...")
        products = Product.objects.all()
        cache.set('products_list', products, timeout=60 * 15)
    else:
        logger.info("Fetching products from cache...")
    return products
