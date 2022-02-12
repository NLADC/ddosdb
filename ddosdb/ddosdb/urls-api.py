from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from . import api

urlpatterns = [
    path('', api.index, name='api-index'),
    # path('fingerprints/', api.fingerprints, name='fingerprints'),
    path('permissions/', api.permissions, name='permissions'),
    path('fingerprint/', api.fingerprints, name='fingerprints'),
    path('fingerprint/<key>', api.fingerprint, name='fingerprint'),
    path('unknown-fingerprints/', api.unknown_fingerprints, name='unknown-fingerprints'),
    path('token/', obtain_auth_token, name='api_token_auth'),
]
