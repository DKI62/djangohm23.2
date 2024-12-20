import json
from django.core.management.base import BaseCommand
from catalog.models import Category, Product


class Command(BaseCommand):
    help = "Load data from JSON fixture into the database"

    def handle(self, *args, **options):
        # Удаляем все объекты
        Product.objects.all().delete()
        Category.objects.all().delete()

        # Загружаем категории
        with open('fixtures/catalog_data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

            categories = [Category(name=item['fields']['name'], description=item['fields']['description']) for item in
                          data if item['model'] == 'catalog.category']
            Category.objects.bulk_create(categories)

            # Загрузим продукты с уже существующими категориями
            products = []
            for item in data:
                if item['model'] == 'catalog.product':
                    category = Category.objects.get(pk=item['fields']['category'])
                    product = Product(
                        name=item['fields']['name'],
                        description=item['fields']['description'],
                        price=item['fields']['price'],
                        category=category
                    )
                    products.append(product)
            Product.objects.bulk_create(products)
