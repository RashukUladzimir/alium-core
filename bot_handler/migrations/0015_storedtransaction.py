# Generated by Django 4.1.5 on 2023-03-10 22:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot_handler', '0014_contract_tokenprice_task_repeatable'),
    ]

    operations = [
        migrations.CreateModel(
            name='StoredTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trx_hash', models.CharField(max_length=200, unique=True)),
            ],
        ),
    ]