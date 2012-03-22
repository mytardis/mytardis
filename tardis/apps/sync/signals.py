from django.dispatch import Signal

transfer_completed = Signal(providing_args=['instance'])
transfer_failed = Signal(providing_args=['instance'])
