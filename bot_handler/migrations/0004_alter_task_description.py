# Generated by Django 4.1.5 on 2023-01-16 16:12

from django.db import migrations
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('bot_handler', '0003_sitesettings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='description',
            field=tinymce.models.HTMLField(),
        ),
    ]
