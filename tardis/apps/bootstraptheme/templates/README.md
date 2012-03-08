# Templates

Put any replacement templates here.

Templates override each other, with an app earlier in ```INSTALLED_APPS``` replacing any overlapping templates in later apps.

## Extending existing templates

If your ```TEMPLATE_LOADERS``` contains ```tardis.template.loader.app-specific.Loader```, then you can extend existing templates by explicitly refering to the app that provides them. For instance, your own ```tardis_portal/portal_template.html``` would probably have this line at the top:

    {% extends "tardis_portal:tardis_portal/portal_template.html" %}

Be careful with explicit extensions, as they won't respect another app overriding the template after yours.
