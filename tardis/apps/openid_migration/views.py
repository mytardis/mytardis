from django.contrib.auth.decorators import login_required, \
    permission_required

from .migration import do_migration, \
    openid_migration_method, \
    confirm_migration


@permission_required('tardis_portal.change_userauthentication')
@login_required()
def migrate_accounts(request):
    '''
    Manage user migration using AJAX.
    '''

    if request.method == 'POST':
        operation = request.POST['operation']
        if operation == 'addAuth':
            return confirm_migration(request)
        if operation == 'migrateAccount':
            return do_migration(request)
    return openid_migration_method(request)
