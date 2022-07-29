from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django_rest_multitokenauth.models import MultiToken
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import GroupAdmin
from django import forms
from ddosdb.models import Query, RemoteDdosDb, MISP, DDoSToken


class CustomUserAdmin(UserAdmin):
    readonly_fields = [
        'date_joined',
        'user_permissions',
    ]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        disabled_fields = set()  # type: Set[str]

        disabled_fields |= {
            'user_permissions',
        }

        if not is_superuser:
            disabled_fields |= {
                'is_superuser',
            }

        # Prevent non-superusers from editing their own permissions
        if (
                not is_superuser
                and obj is not None
                and obj == request.user
        ):
            disabled_fields |= {
                'is_staff',
                'is_superuser',
                'groups',
            }

        # Prevent non-superusers from deactivating superusers
        if (
                not is_superuser
                and obj is not None
                and obj.is_superuser
        ):
            disabled_fields |= {
                'is_active',
                'is_staff',
                'is_superuser',
            }

        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form


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
    list_display = ('name', 'sharing_group', 'active', 'publish', 'push', 'pull', 'url', 'check_cert')
    fields = (('name', 'active', 'publish', 'push', 'pull'), ('url', 'check_cert'), 'authkey', 'sharing_group')

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


class MyGroupAdmin(GroupAdmin):
    change_form_template = 'admin/my_group_change_form.html'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        grp = Group.objects.get(pk=object_id)
        if grp:
            extra_context['group_users'] = ['<NONE>']
            user_list = [user.username for user in User.objects.filter(groups__name=grp.name)]
            if len(user_list) > 0:
                extra_context['group_users'] = user_list
        return super(MyGroupAdmin, self).change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

    def render_change_form(self, request, context, *args, **kwargs):
        # self.change_form_template = 'admin/my_group_change_form.html'
        return super(MyGroupAdmin, self).render_change_form(request, context, *args, **kwargs)


# Register your models here.
admin.site.unregister(MultiToken)
admin.site.unregister(Group)
admin.site.register(Group, MyGroupAdmin)
admin.site.register(DDoSToken, DDoSTokenAdmin)
admin.site.register(RemoteDdosDb, RemoteDdosDbAdmin)
admin.site.register(MISP, MISPAdmin)

# Unregister the provided model admin
admin.site.unregister(User)
# Register out own model admin, based on the default UserAdmin
admin.site.register(User, CustomUserAdmin)
