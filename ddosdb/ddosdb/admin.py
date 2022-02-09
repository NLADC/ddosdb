from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django import forms

from ddosdb.models import Query, AccessRequest, Blame, FileUpload, Profile, RemoteDdosDb, MISP, FailedLogin


# class QueryAdmin(admin.ModelAdmin):
#     list_display = ("user", "query", "timestamp")
#
#
# def allow_access(modeladmin, request, queryset):
#     for access_request in queryset:
#         if not access_request.accepted:
#             password = User.objects.make_random_password()
#
#             send_mail("DDoSDB Access Granted",
#                       """
#             Dear {first_name} {last_name},
#
#             Thank you for your interest. You have been granted access to DDoSDB.
#
#             It is now possible to log in to https://ddosdb.org with the following credentials:
#             Username: {email}
#             Password: {password}
#
#             Yours faithfully,
#
#             The DDoSDB Team
#             """.format(first_name=access_request.first_name,
#                        last_name=access_request.last_name,
#                        email=access_request.email,
#                        password=password),
#                       "noreply@ddosdb.org",
#                       [access_request.email])
#
#             if not User.objects.filter(username=access_request.email).exists():
#                 new_user = User.objects.create_user(username=access_request.email,
#                                                     email=access_request.email,
#                                                     password=password)
#             else:
#                 new_user = User.objects.get(username=access_request.email)
#
#             new_user.first_name = access_request.first_name
#             new_user.last_name = access_request.last_name
#             new_user.set_password(password)
#             new_user.save()
#
#             access_request.accepted = True
#             access_request.save()
#
#
# allow_access.short_description = "Allow access to the selected requests"
#
#
# class AccessRequestAdmin(admin.ModelAdmin):
#     list_display = ("first_name", "last_name", "email", "institution", "timestamp", "accepted")
#     exclude = ("accepted",)
#     ordering = ["accepted", "timestamp"]
#     actions = [allow_access]
#
#
# class BlameAdmin(admin.ModelAdmin):
#     list_display = ("key", "name", "description")
#
#
# class FileUploadAdmin(admin.ModelAdmin):
#     list_display = ("user", "filename", "timestamp")
#
#
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)
#
# #class MyModelAdmin(admin.ModelAdmin):
# #    formfield_overrides = {
# #        models.TextField: {'widget': RichTextEditorWidget},
# #    }


class RemoteDdosDbForm(forms.ModelForm):
    class Meta:
        model = RemoteDdosDb
        fields = []
# Uncommenting code below will give
#        widgets = {
#        'password': forms.PasswordInput(),
#    }


class RemoteDdosDbAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "push", "pull", "url", "check_cert", "username")
    fields = (('name', 'active','push','pull'), ('url','check_cert'), 'username', 'password')

    form = RemoteDdosDbForm


class MISPForm(forms.ModelForm):
    class Meta:
        model = MISP
        fields = []
# Uncommenting code below will give
#        widgets = {
#        'password': forms.PasswordInput(),
#    }


class MISPAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "push", "pull", "url", "check_cert")
    fields = (('name', 'active','push','pull'), ('url','check_cert'), 'authkey')

    form = MISPForm

# class FailedLoginAdmin(admin.ModelAdmin):
#     list_display = ("ipaddress", "logindatetime")
#     fields = ("ipaddress", "logindatetime")
#

# Register your models here.
# admin.site.register(Query, QueryAdmin)
# admin.site.register(AccessRequest, AccessRequestAdmin)
# admin.site.register(Blame, BlameAdmin)
# admin.site.register(FileUpload, FileUploadAdmin)
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(RemoteDdosDb, RemoteDdosDbAdmin)
admin.site.register(MISP, MISPAdmin)
# admin.site.register(FailedLogin, FailedLoginAdmin)