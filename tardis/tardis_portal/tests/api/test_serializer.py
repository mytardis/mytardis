"""
Testing the serializer in the Tastypie-based MyTardis REST API

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
"""
import importlib

from django.test import TestCase


class SerializerTest(TestCase):
    def test_pretty_serializer(self):
        from ...api import PrettyJSONSerializer

        test_serializer = PrettyJSONSerializer()
        test_data = {
            "ugly": "json data",
            "reformatted": 2,
            "be": ["pretty", "and", "indented"],
        }
        test_output = test_serializer.to_json(test_data)
        ref_output = (
            '{\n  "be": [\n    "pretty",\n    "and",\n'
            + '    "indented"\n  ],\n  "reformatted": 2,\n'
            + '  "ugly": "json data"\n}\n'
        )
        self.assertEqual(test_output, ref_output)

    def test_debug_serializer(self):
        with self.settings(DEBUG=False):
            # pylint: disable=import-outside-toplevel
            import tardis.tardis_portal.api

            importlib.reload(tardis.tardis_portal.api)
            self.assertEqual(
                type(tardis.tardis_portal.api.default_serializer).__name__, "Serializer"
            )
        with self.settings(DEBUG=True):
            importlib.reload(tardis.tardis_portal.api)
            self.assertEqual(
                type(tardis.tardis_portal.api.default_serializer).__name__,
                "PrettyJSONSerializer",
            )
