# Generated by Django 5.1.6 on 2025-02-18 11:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collection',
            name='milk_type',
            field=models.CharField(choices=[('cow', 'Cow'), ('buffalo', 'Buffalo'), ('mix', 'Mix')], db_index=True, max_length=10),
        ),
    ]
