# Celery queue

# Use a strong password for production, but guest credentials are OK for
# local development:
BROKER_URL = 'amqp://guest:guest@localhost:5672//'

# For local development, you can force Celery tasks to run synchronously:
# CELERY_ALWAYS_EAGER = True
# CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
