from .migration import do_migration, add_auth_method


def migrate_accounts(request):
    """

    :param request:
    :return:
    """
    from .migration import list_auth_methods

    if request.method == 'POST':
        operation = request.POST['operation']
        if operation == 'addAuth':
            return add_auth_method(request)
        elif operation == 'mergeAuth':
            return do_migration(request)
    # if GET, we'll just give the initial list of auth methods for the user
    return list_auth_methods(request)
