# Generated by Django 5.1.7 on 2025-04-10 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0006_alter_stock_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='comment',
            field=models.TextField(blank=True, help_text='Additional notes about the order', null=True),
        ),
    ]
