from django.db import models
from django_rest_multitokenauth.models import MultiToken
from django.contrib.auth.models import User


class Query(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True)
    query = models.TextField()


class Fingerprint(models.Model):
    class Meta:
        managed = False

        permissions = [
            ('upload_fingerprint', 'Can upload fingerprints'),
            ('view_nonsync_fingerprint', 'Can view non-shared fingerprints'),
            ('edit_comment_fingerprint', 'Can edit comments of fingerprints'),
            ('edit_sync_fingerprint', 'Can change shareability of fingerprints'),
        ]


class RemoteDdosDb(models.Model):
    class Meta:
        verbose_name_plural = " Remote DDoS-DBs"

    name = models.CharField('Remote DDoS-DB name', max_length=255,
                            help_text="""A friendly name for the remote repository""")
    url = models.URLField('Remote DDoS-DB URL',
                          help_text="""The base URL for the remote sync API""")
    authkey = models.CharField('Authentication Key', max_length=255,
                               help_text="""Authorization Token for the remote DDoSDB API""")
    active = models.BooleanField(default=True,
                                 help_text="""Check this to sync with this DDoS-DB""")
    push = models.BooleanField(default=False,
                               help_text="""Sync towards this DDoS-DB""")
    pull = models.BooleanField(default=True,
                               help_text="""Sync from this DDoS-DB""")

    check_cert = models.BooleanField(default=True,
                                     help_text="""Whether to check remote DDoS-DB certificate on https""")

    def save(self, *args, **kwargs):
        if not self.url.endswith('/'):
            self.url = "{}/".format(self.url)
        return super(RemoteDdosDb, self).save(*args, **kwargs)

    def __str__(self):
        postfix = ' (inactive)'
        if (self.active):
            postfix = ''
        return self.name + postfix


class MISP(models.Model):
    class Meta:
        verbose_name_plural = " MISPs"

    name = models.CharField('MISP name', max_length=255,
                            help_text="""A friendly name for the MISP instance""")
    url = models.URLField('MISP URL',
                          help_text="""The base URL for the MISP""")
    authkey = models.CharField('Authentication Key', max_length=255,
                               help_text="""Authentication key for the MISP Automation API""")
    active = models.BooleanField(default=True,
                                 help_text="""Check this to sync with this MISP""")
    push = models.BooleanField(default=True,
                               help_text="""Sync towards this MISP""")
    pull = models.BooleanField(default=False,
                               help_text="""Sync from this MISP""")

    check_cert = models.BooleanField(default=True,
                                     help_text="""Whether to check remote certificate on https""")

    sharing_group = models.CharField('Sharing Group', max_length=255, default="", blank=True,
                               help_text="""(Optional) Sharing Group to Distribute to, leave empty for default""")

    def __str__(self):
        postfix = ' (inactive)'
        if (self.active):
            postfix = ''
        return self.name + postfix


class DDoSToken(MultiToken):

    class Meta:
        verbose_name = "Token"
        verbose_name_plural = "Tokens"
        permissions = [
            ('add_own_token', 'Can add own Tokens'),
            ('view_own_token', 'Can view own Tokens'),
            ('delete_own_token', 'Can delete own Tokens'),
        ]

    description = models.CharField(
        max_length=256,
        verbose_name="Description",
        default=""
    )

    def __str__(self):
        return "{} (user {} with description  {})".format(
            self.key, self.user, self.description
        )
