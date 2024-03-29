# Generated by Django 4.1.5 on 2023-02-05 13:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bot_handler', '0007_alter_proof_image_answer'),
    ]

    operations = [
        migrations.CreateModel(
            name='Validator',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('expression', models.CharField(max_length=50)),
            ],
        ),
        migrations.RemoveField(
            model_name='client',
            name='referral_link',
        ),
        migrations.AddField(
            model_name='task',
            name='validator',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bot_handler.validator'),
        ),
    ]
