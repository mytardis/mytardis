# pylint: disable=W1114
from django.db import transaction

from tardis.apps.openid_migration.migration import (
    migrate_api_key,
    migrate_user_permissions,
)
from tardis.tardis_portal.models import Group


def rollback_migration(user_migration_obj):
    # get old user, new user
    new_user = user_migration_obj.new_user
    old_user = user_migration_obj.old_user

    # get object ACls updated by this migration
    migrated_acls_records = user_migration_obj.openidaclmigration_set.all()
    # for each migrated ACLs revert it back to old user and delete acl migration record

    for migrated_acls_record in migrated_acls_records:
        # get migrated ACL
        acl = migrated_acls_record.acl_id
        acl.entityId = old_user.id
        acl.save()
        migrated_acls_record.delete()

    # set new user to inactive and old user to active
    new_user.is_active = False
    old_user.is_active = True
    # set user_migration status to false
    user_migration_obj.migration_status = False
    user_migration_obj.save()

    # roll back group changes
    groups = Group.objects.filter(user=new_user)
    for group in groups:
        old_user.groups.add(group)
    # roll back permission changes
    migrate_user_permissions(
        new_user, old_user
    )  # pylint: disable=arguments-out-of-order
    # roll back api key
    migrate_api_key(new_user, old_user)  # pylint: disable=arguments-out-of-order
    # delete new account
    with transaction.atomic():
        new_user.delete()
        # remove _{authmethod} from old user's account name
        old_user.username = old_user.username.split("_")[0]
        old_user.save()
