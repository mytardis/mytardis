def migrate_accounts(request):
    from tardis.tardis_portal.auth.authentication import add_auth_method, \
        merge_auth_method, remove_auth_method, edit_auth_method, \
        list_auth_methods

    return list_auth_methods(request)
