# Generated by Django 5.1.1 on 2024-12-12 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0007_product_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='publish_status',
            field=models.CharField(choices=[('draft', 'Черновик'), ('published', 'Опубликован'), ('unpublished', 'Снято с публикации')], default='draft', max_length=20, verbose_name='Статус публикации'),
        ),
    ]
