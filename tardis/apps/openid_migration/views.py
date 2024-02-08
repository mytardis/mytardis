from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.debug import sensitive_post_parameters

from .migration import confirm_migration, do_migration, openid_migration_method


@sensitive_post_parameters("password")
@permission_required("openid_migration.add_openidusermigration")
@login_required()
def migrate_accounts(request):
    """
    Manage user migration using AJAX.
    """

    if request.method == "POST":
        operation = request.POST["operation"]
        if operation == "addAuth":
            return confirm_migration(request)
        if operation == "migrateAccount":
            return do_migration(request)
    return openid_migration_method(request)
