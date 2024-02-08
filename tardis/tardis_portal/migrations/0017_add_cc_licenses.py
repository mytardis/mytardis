# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import warnings

from django.db import migrations
from django.db.utils import IntegrityError

from tardis.tardis_portal.models.license import License

LICENSES = [
    {
        "fields": {
            "name": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
            "url": "https://creativecommons.org/licenses/by/4.0/",
            "internal_description": "This licence lets others distribute, remix, tweak, and build upon your work, even commercially, as long as they credit you for the original creation. This is the most accommodating of licences offered under Creative Commons.",
            "image_url": "https://licensebuttons.net/l/by/4.0/88x31.png",
        }
    },
    {
        "fields": {
            "name": "Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)",
            "url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "internal_description": "This licence lets others remix, tweak, and build upon your work even for commercial purposes, as long as they credit you and licence their new creations under the identical terms.",
            "image_url": "https://licensebuttons.net/l/by-sa/4.0/88x31.png",
        }
    },
    {
        "fields": {
            "name": "Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)",
            "url": "https://creativecommons.org/licenses/by-nc/4.0/",
            "internal_description": "This licence lets others remix, tweak, and build upon your work non-commercially, and although their new works must also acknowledge you and be non-commercial, they don't have to licence their derivative works on the same terms.",
            "image_url": "https://licensebuttons.net/l/by-nc/4.0/88x31.png",
        }
    },
    {
        "fields": {
            "name": "Creative Commons Attribution-NoDerivatives 4.0 International (CC BY-ND 4.0)",
            "url": "https://creativecommons.org/licenses/by-nd/4.0/",
            "internal_description": "This licence allows for redistribution, commercial and non-commercial, as long as it is passed along unchanged and in whole, with credit to you.",
            "image_url": "https://licensebuttons.net/l/by-nd/4.0/88x31.png",
        }
    },
    {
        "fields": {
            "name": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
            "url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
            "internal_description": "This licence lets others remix, tweak, and build upon your work non-commercially, as long as they credit you and licence their new creations under the identical terms.",
            "image_url": "https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png",
        }
    },
    {
        "fields": {
            "name": "Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)",
            "url": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
            "internal_description": "This licence is the most restrictive Creative Commons licence, only allowing others to download your works and share them with others as long as they credit you, but they can't change them in any way or use them commercially.",
            "image_url": "https://licensebuttons.net/l/by-nc-nd/4.0/88x31.png",
        }
    },
]


def forwards_func(apps, schema_editor):
    load_licenses(apps, schema_editor)


def reverse_func(apps, schema_editor):
    remove_licenses(apps, schema_editor)


def load_licenses(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    for license in LICENSES:
        try:
            License.objects.using(db_alias).get_or_create(
                name=license["fields"]["name"],
                url=license["fields"]["url"],
                is_active=True,
                allows_distribution=True,
                internal_description=license["fields"]["internal_description"],
                image_url=license["fields"]["image_url"],
            )
        except IntegrityError:
            warnings.warn(
                "License '%s' already exists in the database"
                % license["fields"]["name"]
            )


def remove_licenses(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    for license in LICENSES:
        try:
            License.objects.using(db_alias).get(name=license["fields"]["name"]).delete()
        except License.DoesNotExist:
            warnings.warn(
                "License '%s' was not found in the database" % license["fields"]["name"]
            )


class Migration(migrations.Migration):

    dependencies = [
        ("tardis_portal", "0016_add_timestamps"),
        ("auth", "0008_alter_user_username_max_length"),
    ]

    operations = [migrations.RunPython(forwards_func, reverse_func)]
