from os import path

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            path.join(path.dirname(__file__), "..", "tardis_portal/templates/").replace(
                "\\", "/"
            ),
        ],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.static",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "tardis.tardis_portal.context_processors.global_contexts",
                "tardis.tardis_portal.context_processors.single_search_processor",
                "tardis.tardis_portal.context_processors.registration_processor",
                "tardis.tardis_portal.context_processors.user_details_processor",
                "tardis.tardis_portal.context_processors.google_analytics",
                "tardis.tardis_portal.context_processors.user_menu_processor",
                "tardis.tardis_portal.context_processors.project_app_processor",
            ],
            "loaders": [
                (
                    "django.template.loaders.cached.Loader",
                    [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ],
                ),
            ],
        },
    }
]
