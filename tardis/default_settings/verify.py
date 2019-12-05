# File verification configuration

VERIFY_AS_SERVICE = False
'''
If enabled, a task will be sent to RabbitMQ after a file is saved to verify
checksum by decoupled microservice (to be run separately).
'''

VERIFY_DEFAULT_PRIORITY = 8
'''
The default RabbitMQ task priority for messages sent to the verify service.
'''

VERIFY_DEFAULT_ALGORITHM = 'md5'
'''
While MyData will send checksum algorithm, this setting is required for POST.
'''
