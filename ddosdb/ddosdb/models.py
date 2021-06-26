from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from website import settings

class Query(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True)
    query = models.TextField()


class AccessRequest(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=150)
    institution = models.CharField(max_length=100)
    purpose = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True, blank=True)
    accepted = models.BooleanField(default=False)


class Blame(models.Model):
    key = models.CharField(max_length=32)
    name = models.CharField(max_length=150)
    description = models.TextField(default="")

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description
        }


class Fingerprint(models.Model):
    class Meta:
        managed = False

        permissions = (
            ('upload_fingerprint', 'Can upload fingerprints'),
        )


class FileUpload(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True)
    filename = models.CharField(max_length=200)

    def save(self, *args, **kwargs):
        # if not self.pk:
        #     send_mail("DDoSDB File Uploaded",
        #               """
        #     User: {user}
        #     File name: {filename}
        #     Timestamp: {timestamp}
        #     """.format(user=self.user.username,
        #                filename=self.filename,
        #                timestamp=self.timestamp),
        #               "noreply@ddosdb.org",
        #               [settings.ACCESS_REQUEST_EMAIL])

        super(FileUpload, self).save(*args, **kwargs)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    institution = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username


class RemoteDdosDb(models.Model):
    class Meta:
        verbose_name_plural = " Remote DDoS-DBs"

    name = models.CharField('Remote DDoS-DB name', max_length=255,
        help_text="""A friendly name for the remote repository""")
    url = models.URLField('Remote DDoS-DB URL',
        help_text="""The base URL for the remote sync API""")
    username = models.CharField('username', max_length=255)
    password = models.CharField(max_length=255)
    active   = models.BooleanField(default=False,
        help_text="""Activate to sync local fingerprints with this DDoS-DB""")

    check_cert   = models.BooleanField(default=True,
        help_text="""Whether to check remote DDoS-DB certificate on https""")

    def __str__(self):
        postfix = ' (inactive)'
        if (self.active):
            postfix = ''
        return self.name+postfix

class FailedLogin(models.Model):
    class Meta:
        verbose_name_plural = " Failed logins"

    ipaddress = models.CharField('IP Address', max_length=255,
        help_text="""The IP address the login was from""")
    logindatetime = models.DateTimeField('DateTime of failed login',
        help_text="""The time and date of failed login""")

    def __str__(self):
        return self.ipaddress

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created or not Profile.objects.filter(user=instance).exists():
        instance.profile = Profile.objects.create(user=instance)
    instance.profile.save()
