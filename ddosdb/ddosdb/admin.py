from django.contrib import admin
from django_rest_multitokenauth.models import MultiToken
from django import forms
from ddosdb.models import Query, RemoteDdosDb, MISP, DDoSToken


class RemoteDdosDbForm(forms.ModelForm):
    class Meta:
        model = RemoteDdosDb
        fields = []


class RemoteDdosDbAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "push", "pull", "url", "check_cert")
    fields = (('name', 'active','push','pull'), ('url','check_cert'), 'authkey')

    form = RemoteDdosDbForm

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['url'].widget.attrs['placeholder'] = "https://remote.ddosdb.url/"
        return form


class MISPForm(forms.ModelForm):
    class Meta:
        model = MISP
        fields = []


class MISPAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "push", "pull", "url", "check_cert")
    fields = (('name', 'active','push','pull'), ('url','check_cert'), 'authkey')

    form = MISPForm

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['url'].widget.attrs['placeholder'] = "https://remote.misp.url/"
        return form


class DDoSTokenAdmin(admin.ModelAdmin):
    exclude = ['key']
    readonly_fields = ['key']
    list_display = ('key', 'user', 'description',)
    fields = (('key', 'user','description'))


# Register your models here.
# admin.site.unregister(MultiToken)
admin.site.register(DDoSToken, DDoSTokenAdmin)
admin.site.register(RemoteDdosDb, RemoteDdosDbAdmin)
admin.site.register(MISP, MISPAdmin)

