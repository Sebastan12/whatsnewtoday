# Generated by Django 4.0.4 on 2022-05-31 15:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrapper', '0004_image_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='hash',
            field=models.CharField(default=None, max_length=255),
            preserve_default=False,
        ),
    ]
