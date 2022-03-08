#import django.contrib.auth.views
from django.urls import include, path
from . import views, api

urlpatterns = [
    path('', views.index, name='index'),
    path('about', views.about, name='about'),
    path('help', views.help_page, name='help'),
    path('login', views.signin, name='login'),
    # path('request-access', views.request_access, name='request-access'),
    path('account', views.account, name='account'),
    path('groups', views.groups, name='groups'),
    path('tokens', views.tokens, name='tokens'),
    path('delete-token', views.delete_token, name='delete-token'),
    path('logout', views.signout, name='logout'),
    path('query', views.query, name='query'),
    path('details', views.details, name='details'),
    path('download', views.download, name='download'),
    # path('compare', views.compare, name='compare'),
    path('upload-file', views.upload_file, name='upload-file'),
    path('overview', views.overview, name='overview'),
    path('delete', views.delete, name='delete'),
    path('remote-sync', views.remote_sync, name='remote-sync'),
    path('misp-sync', views.misp_sync, name='misp-sync'),
    path('edit-comment', views.edit_comment, name='edit-comment'),
    path('toggle-shareable', views.toggle_shareable, name='toggle-shareable'),
    path('my-permissions', views.my_permissions, name='my-permissions'),
    path('fingerprints', views.fingerprints, name='fingerprints'),
    path('unknown-fingerprints', views.unknown_fingerprints, name='unknown-fingerprints'),
    path('fingerprint/<key>', views.fingerprint, name='fingerprint'),
    path('remote-dbs', views.remote_dbs, name='remote-dbs'),
    path('attack-trace/<key>', views.attack_trace, name='attack-trace'),
    path('csp-report', views.csp_report, name='csp-report'),

]
