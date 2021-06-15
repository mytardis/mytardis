from django.apps import apps
from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User

from tardis.tardis_portal.models.access_control import ExperimentACL

from .apps import OpenidMigrationConfig


class OpenidUserMigration(models.Model):
    old_user = models.ForeignKey(User, null=True, related_name='old_user',
                                 on_delete=models.CASCADE)
    old_user_auth_method = models.CharField(null=False, blank=False, max_length=30)
    new_user = models.ForeignKey(User, null=True, related_name='new_user',
                                 on_delete=models.CASCADE)
    new_user_auth_method = models.CharField(null=False, blank=False, max_length=30)
    migration_timestamp = models.DateTimeField(auto_now_add=True)
    migration_status = models.BooleanField(default=False)

    class Meta:
        app_label = 'openid_migration'

    def __str__(self):
        return '%s | %s' % (self.old_user.username, self.new_user.username)


class OpenidACLMigration(models.Model):
    user_migration = models.ForeignKey(OpenidUserMigration, on_delete=models.CASCADE)
    acl_id = models.ForeignKey(ExperimentACL, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        app_label = 'openid_migration'

    def __str__(self):
        if self.acl_id:
            return '%s | %s' % (self.user_migration, self.acl_id)
        else:
            return '%s | %s' % (self.user_migration, "old ACL no longer exists")


class OpenidACLMigrationAdmin(admin.ModelAdmin):
    list_display = [
        'user_migration_obj', 'acl_id'
    ]

    def user_migration_obj(self, obj):
        return obj.user_migration


class OpenidUserMigrationAdmin(admin.ModelAdmin):
    list_display = [
        '__str__', 'old_user', 'old_user_auth_method', 'new_user_id',
        'new_user_auth_method', 'migration_timestamp', 'migration_status'
    ]


# register
if apps.is_installed(OpenidMigrationConfig.name):
    admin.site.register(OpenidUserMigration, OpenidUserMigrationAdmin)
    admin.site.register(OpenidACLMigration, OpenidACLMigrationAdmin)
