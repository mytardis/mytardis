from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

from tardis.tardis_portal.managers import OracleSafeManager

from .experiment import Experiment

import logging
logger = logging.getLogger(__name__)

def _token_expiry():
    import datetime as dt
    return dt.datetime.now().date() + dt.timedelta(settings.TOKEN_EXPIRY_DAYS)

class Token(models.Model):

    token = models.CharField(max_length=30, unique=True)
    experiment = models.ForeignKey(Experiment)

    expiry_date = models.DateField(default=_token_expiry)

    user = models.ForeignKey(User)

    _TOKEN_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    objects = OracleSafeManager()

    class Meta:
        app_label = 'tardis_portal'

    def __unicode__(self):
        return '%s %s' % (self.expiry_date, self.token)

    def _randomise_token(self):
        from random import choice
        self.token = ''.join(choice(self._TOKEN_CHARS)
                                for _ in range(settings.TOKEN_LENGTH))

    def save_with_random_token(self):
        from django.db import IntegrityError

        if not self.user or not self.experiment:  # fail if success impossible
            self.save()

        for _ in range(30):  # 30 is an arbitrary number
            self._randomise_token()
            try:
                logger.debug(self.token)
                self.save()
            except IntegrityError as e:
                logger.debug(e)
                continue
            else:
                return
        logger.warning('failed to generate a random token')
        self.save()  # give up and raise the exception

    @models.permalink
    def get_absolute_url(self):
        return ('tardis.tardis_portal.views.token_login', (),
                {'token': self.token})

    def is_expired(self):
        import datetime as dt
        return self.expiry_date and self.expiry_date < dt.datetime.now().date()

    def _get_expiry_as_datetime(self):
        import datetime as dt
        exp = self.expiry_date
        return dt.datetime(exp.year, exp.month, exp.day, 23, 59, 59)

    @staticmethod
    def _tomorrow_4am():
        import datetime as dt
        today = dt.datetime.now().date()
        tomorrow = today + dt.timedelta(1)
        tomorrow_4am = dt.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 4)
        return tomorrow_4am

    def get_session_expiry(self):
        '''
            A token login should expire at the earlier of
            a) tomorrow at 4am
            b) the (end of) the token's expiry date

            It is the responsibility of token_auth to set the session expiry
        '''
        if self.is_expired():
            import datetime as dt
            return dt.datetime.now()

        expire_tomorrow_morning = self._tomorrow_4am()
        token_as_datetime = self._get_expiry_as_datetime()

        print expire_tomorrow_morning
        print token_as_datetime

        if expire_tomorrow_morning < token_as_datetime:
            return expire_tomorrow_morning
        else:
            return token_as_datetime
