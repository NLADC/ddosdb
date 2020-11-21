# Generated by Django 3.1 on 2020-11-20 19:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ddosdb', '0012_remoteddosdb_active'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='remoteddosdb',
            options={'verbose_name_plural': ' Remote DDoS-DBs'},
        ),
        migrations.AlterField(
            model_name='remoteddosdb',
            name='api_url',
            field=models.URLField(verbose_name='Remote DDoS-DB URL'),
        ),
    ]
