from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from . import api

urlpatterns = [
    path('permissions/', api.permissions, name='permissions'),
    path('fingerprint/', api.fingerprints, name='fingerprints'),
    path('fingerprint/<key>', api.fingerprint, name='fingerprint'),
    path('unknown-fingerprints/', api.unknown_fingerprints, name='unknown-fingerprints'),
]
