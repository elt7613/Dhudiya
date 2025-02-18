# Generated by Django 5.1.6 on 2025-02-18 08:14

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(db_index=True, max_length=13, unique=True, validators=[django.core.validators.RegexValidator(message='Phone number must be a 10-digit number starting with 6-9.', regex='^[1-9]\\d{9}$')]),
        ),
    ]
