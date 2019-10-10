# File verification configuration

VERIFY_AS_SERVICE = False
'''
If enabled, a task will be sent to RabbitMQ after a file is saved to verify
checksum by decoupled microservice (to be run separately).
'''
