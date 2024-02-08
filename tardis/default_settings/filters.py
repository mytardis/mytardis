# Filters configuration

USE_FILTERS = False
"""
If enabled, a task will be sent to RabbitMQ after a file is saved and verified,
requesting post-processing, e.g. extracting metadata from file headers and/or
generating thumbnail images.
"""

FILTERS_TASK_PRIORITY = 4
"""
The default RabbitMQ task priority for messages sent to the filters
microservice.  Priority 4 is slightly less than the overall default
task priority of 5, defined in tardis/default_settings/celery_settings.py
"""
