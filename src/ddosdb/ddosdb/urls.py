import django.contrib.auth.views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about', views.about, name='about'),
    path('help', views.help_page, name='help'),
    path('login', views.signin, name='login'),
    path('request-access', views.request_access, name='request-access'),
    path('account', views.account, name='account'),
    path('logout', views.signout, name='logout'),
    path('query', views.query, name='query'),
    path('compare', views.compare, name='compare'),
    path('fingerprint/<key>', views.fingerprint, name='fingerprint'),
    path('attack-trace/<key>', views.attack_trace, name='attack-trace'),
    path('upload-file', views.upload_file, name='upload-file'),
    path('overview', views.overview, name='overview'),
]
