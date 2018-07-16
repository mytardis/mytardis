from .migration import do_migration, \
    openid_migration_method, \
    confirm_migration


def migrate_accounts(request):
    """
    :param request:
    :return:
    """

    if request.method == 'POST':
        operation = request.POST['operation']
        if operation == 'addAuth':
            return confirm_migration(request)
        if operation == 'migrateAccount':
            return do_migration(request)
    return openid_migration_method(request)


