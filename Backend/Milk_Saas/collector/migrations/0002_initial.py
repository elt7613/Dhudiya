# Generated by Django 5.1.6 on 2025-02-18 08:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('collector', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='customer',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='collection',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='collector.customer'),
        ),
        migrations.AddField(
            model_name='dairyinformation',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='marketmilkprice',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name='customer',
            index=models.Index(fields=['name', 'phone'], name='collector_c_name_2644ba_idx'),
        ),
        migrations.AddIndex(
            model_name='customer',
            index=models.Index(fields=['author', 'is_active'], name='collector_c_author__f481e7_idx'),
        ),
        migrations.AddIndex(
            model_name='collection',
            index=models.Index(fields=['collection_date', 'collection_time'], name='collector_c_collect_3fda75_idx'),
        ),
        migrations.AddIndex(
            model_name='collection',
            index=models.Index(fields=['customer', 'collection_date'], name='collector_c_custome_826b31_idx'),
        ),
        migrations.AddIndex(
            model_name='collection',
            index=models.Index(fields=['author', 'is_active', 'collection_date'], name='collector_c_author__5f52a4_idx'),
        ),
        migrations.AddIndex(
            model_name='collection',
            index=models.Index(fields=['milk_type', 'collection_date'], name='collector_c_milk_ty_7ba5c5_idx'),
        ),
        migrations.AddIndex(
            model_name='collection',
            index=models.Index(fields=['rate', 'amount'], name='collector_c_rate_068452_idx'),
        ),
        migrations.AddIndex(
            model_name='dairyinformation',
            index=models.Index(fields=['dairy_name', 'rate_type'], name='collector_d_dairy_n_7f4133_idx'),
        ),
        migrations.AddIndex(
            model_name='dairyinformation',
            index=models.Index(fields=['author', 'is_active', 'created_at'], name='collector_d_author__5924d0_idx'),
        ),
        migrations.AddIndex(
            model_name='marketmilkprice',
            index=models.Index(fields=['price', 'created_at'], name='collector_m_price_6e9d0a_idx'),
        ),
        migrations.AddIndex(
            model_name='marketmilkprice',
            index=models.Index(fields=['author', 'is_active', 'created_at'], name='collector_m_author__17dd92_idx'),
        ),
    ]
