# Generated by Django 2.2.19 on 2021-03-20 23:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_issued_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='issued_at',
            field=models.DateTimeField(auto_now_add=True, help_text='Date time after wich tokens are valid .', verbose_name='issued at'),
        ),
    ]
