import datetime
import logging
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

from ..managers import OracleSafeManager

from .experiment import Experiment

logger = logging.getLogger(__name__)


def _token_expiry():
    return (datetime.datetime.now().date() +
            datetime.timedelta(settings.TOKEN_EXPIRY_DAYS))


class Token(models.Model):

    token = models.CharField(max_length=30, unique=True)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)

    expiry_date = models.DateField(default=_token_expiry)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    _TOKEN_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    objects = OracleSafeManager()

    class Meta:
        app_label = 'tardis_portal'

    def __str__(self):
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

    def is_expired(self):
        return (self.expiry_date and
                self.expiry_date < datetime.datetime.now().date())

    def _get_expiry_as_datetime(self):
        exp = self.expiry_date
        return datetime.datetime(exp.year, exp.month, exp.day, 23, 59, 59)

    @staticmethod
    def _tomorrow_4am():
        today = datetime.datetime.now().date()
        tomorrow = today + datetime.timedelta(1)
        tomorrow_4am = datetime.datetime(
            tomorrow.year, tomorrow.month, tomorrow.day, 4)
        return tomorrow_4am

    def get_session_expiry(self):
        '''
            A token login should expire at the earlier of
            a) tomorrow at 4am
            b) the (end of) the token's expiry date

            It is the responsibility of token_auth to set the session expiry
        '''
        if self.is_expired():
            return datetime.datetime.now()

        expire_tomorrow_morning = self._tomorrow_4am()
        token_as_datetime = self._get_expiry_as_datetime()

        if expire_tomorrow_morning < token_as_datetime:
            return expire_tomorrow_morning
        return token_as_datetime
