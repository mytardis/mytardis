from tardis.default_settings import USER_MENU_MODIFIERS

OPENID_MIGRATION_EMAIL_MESSAGES = {
    'migration_complete': ('[{site_title}] User Migration Completed Successfully',
                           '''\
Dear {firstname} {lastname},

The process of migrating all your settings and data \
to your "{auth_method}" account ({user_name}) \
has been completed successfully. Your old account has been disabled. \
Please use "{auth_method}" for your future interactions with {site_title}.

Please contact {support_email} if you did not \
request to migrate your account or if you think you received this email by error.

Regards,
{site_title} Team.
'''),
}

USER_MENU_MODIFIERS.extend([
    'tardis.apps.openid_migration.user_menu_modifiers.add_migrate_account_menu_item'
])
'''
Adds a Migrate My Account menu item to the user menu.
'''

ACCOUNT_MIGRATION_INSTRUCTIONS_LINKS = {
    "google": "",
    "aaf": "",
}
