from django.db import models
from django.utils.text import slugify
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name='Наименование')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    PUBLISH_STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликован'),
        ('unpublished', 'Снято с публикации')
    ]

    name = models.CharField(max_length=200, verbose_name='Наименование')
    description = models.TextField(blank=True, verbose_name='Описание')
    image = models.ImageField(upload_to='products/', verbose_name='Изображение (превью)', blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name='Категория')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена за покупку')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата последнего изменения')

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Владелец',
        null=True,
        blank=True
    )
    publish_status = models.CharField(
        max_length=20,
        choices=PUBLISH_STATUS_CHOICES,
        default='draft',
        verbose_name='Статус публикации'
    )

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        permissions = [
            ("can_unpublish_product", "Can unpublish product"),
            ("can_edit_product_description", "Can edit product description"),
            ("can_change_product_category", "Can change product category"),
        ]

    def __str__(self):
        return self.name

    def get_active_version(self):
        active_version = self.versions.filter(is_active=True).first()  # Получаем активную версию
        return active_version


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()
    preview = models.ImageField(upload_to='blog_previews/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    views_count = models.PositiveIntegerField(default=0)  # Счетчик просмотров
    is_published = models.BooleanField(default=False)  # Признак публикации

    class Meta:
        verbose_name = 'Блоговая запись'
        verbose_name_plural = 'Блоговые записи'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Version(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='versions')
    version_number = models.CharField(max_length=50)  # Номер версии
    version_name = models.CharField(max_length=255)  # Название версии
    is_active = models.BooleanField(default=False)  # Признак текущей версии

    def __str__(self):
        return f"{self.product.name} - {self.version_name}  {self.version_number}"

    class Meta:
        unique_together = ('product', 'is_active')  # Обеспечиваем, чтобы был только один активный продукт
