# Generated by Django 3.2.12 on 2022-02-12 22:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Fingerprint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'permissions': (('upload_fingerprint', 'Can upload fingerprints'),),
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='FailedLogin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ipaddress', models.CharField(help_text='The IP address the login was from', max_length=255, verbose_name='IP Address')),
                ('logindatetime', models.DateTimeField(help_text='The time and date of failed login', verbose_name='DateTime of failed login')),
            ],
            options={
                'verbose_name_plural': ' Failed logins',
            },
        ),
        migrations.CreateModel(
            name='MISP',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='A friendly name for the MISP instance', max_length=255, verbose_name='MISP name')),
                ('url', models.URLField(help_text='The base URL for the MISP', verbose_name='MISP URL')),
                ('authkey', models.CharField(help_text='Authentication key for the MISP Automation API', max_length=255, verbose_name='Authentication Key')),
                ('active', models.BooleanField(default=True, help_text='Check this to sync with this MISP')),
                ('push', models.BooleanField(default=True, help_text='Sync towards this MISP')),
                ('pull', models.BooleanField(default=False, help_text='Sync from this MISP')),
                ('check_cert', models.BooleanField(default=True, help_text='Whether to check remote certificate on https')),
            ],
            options={
                'verbose_name_plural': ' MISPs',
            },
        ),
        migrations.CreateModel(
            name='RemoteDdosDb',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='A friendly name for the remote repository', max_length=255, verbose_name='Remote DDoS-DB name')),
                ('url', models.URLField(help_text='The base URL for the remote sync API', verbose_name='Remote DDoS-DB URL')),
                ('username', models.CharField(max_length=255, verbose_name='username')),
                ('password', models.CharField(max_length=255)),
                ('active', models.BooleanField(default=True, help_text='Check this to sync with this DDoS-DB')),
                ('push', models.BooleanField(default=False, help_text='Sync towards this DDoS-DB')),
                ('pull', models.BooleanField(default=True, help_text='Sync from this DDoS-DB')),
                ('check_cert', models.BooleanField(default=True, help_text='Whether to check remote DDoS-DB certificate on https')),
            ],
            options={
                'verbose_name_plural': ' Remote DDoS-DBs',
            },
        ),
        migrations.CreateModel(
            name='Query',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('query', models.TextField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('institution', models.CharField(max_length=100)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
