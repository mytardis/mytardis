from django.dispatch import Signal

received_remote = Signal(providing_args=['instance', 'uid','from_url'])
