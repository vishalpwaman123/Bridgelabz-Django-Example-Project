# Generated by Django 3.0.7 on 2020-06-30 11:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20200630_0005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='register',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
