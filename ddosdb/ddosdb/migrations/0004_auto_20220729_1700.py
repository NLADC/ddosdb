# Generated by Django 3.2.14 on 2022-07-29 17:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ddosdb', '0003_alter_misp_sharing_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='misp',
            name='publish',
            field=models.BooleanField(default=False, help_text='Automatically publish exported fingerprints'),
        ),
        migrations.AlterField(
            model_name='misp',
            name='sharing_group',
            field=models.CharField(blank=True, default='', help_text='(Optional) Sharing Group to Distribute to, leave empty for default', max_length=255, verbose_name='Sharing Group'),
        ),
    ]
