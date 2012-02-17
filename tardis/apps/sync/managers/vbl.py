from django.conf import settings
from suds.client import Client
import json
from datetime import datetime
import logging

from default_manager import SyncManager


logger = logging.getLogger(__file__)


class VBLSyncManager(SyncManager):
    def __init__(self):
        super(VBLSyncManager, self).__init__(self, institution='AS')


    def _start_file_transfer(self, exp, ssp):
        epn = _get_epn_from_exp(exp)

        client = Client(settings.VBLSTORAGEGATEWAY, cache=None)

        x509 = ssp.getTransferSetting('password')

        # build destination path
        dirname = os.path.abspath(
            os.path.join(ssp.getTransferSetting('serversite'),  'wheredoiputit')
            )
        logger.debug('destination url:  %s' % ssp.getTransferSetting('sl'))
        logger.debug('destination path: %s' % dirname)

        # contact VBL
        key = client.service.VBLstartTransferGridFTP(
            ssp.getTransferSetting('user'),
            x509,
            epn,
            '/Frames\\r\\nTARDIS\\r\\n',
            ssp.getTransferSetting('sl'),
            dirname,
            ssp.getTransferSetting('optionFast'),
            ssp.getTransferSetting('optionPenable'),
            ssp.getTransferSetting('optionP'),
            ssp.getTransferSetting('optionBSenable'),
            ssp.getTransferSetting('optionBS'),
            ssp.getTransferSetting('optionTCPBenable'),
            ssp.getTransferSetting('optionTCPBS'))

        if key.startswith('Error:'):
            logger.error('[vbl] %s: epn %s' % (key, epn))
            raise SyncManagerTransferError(key)
        else:
            logger.info('[vbl] %s: pn %s' % (key, epn))


    def _get_status(self, exp):
        epn = _get_epn_from_exp(exp)

        try:
            # Switch the suds cache off, otherwise suds will try to
            # create a tmp directory in /tmp. If it already exists but
            # has the wrong permissions, the authentication will fail.
            client = Client(settings.VBLTARDISINTERFACE, cache=None)
        except suds.WebFault as detail:
            logger.error('VBLTARDISINTERFACE SOAP error: %s' % detail)
            raise SyncManagerTransferError('VBL error: %s' % detail)

        result = str(client.service.VBLgetTransferStatus(epn))
        try:
            result_dict = json.loads(result)
        except ValueError:
            logger.warning('VBLgetTransferStatus returned invalid JSON: %s' % result)
            result_dict = None
            raise SyncManagerTransferError('VBL error: %s' % result)
        return result_dict


def _get_epn_from_exp(self, exp):
    try:
        # get EPN (needed to kick-off vbl gridftp transfer)
        epn = ExperimentParameter.objects.get(parameterset__experiment=exp,
                                              name__name='EPN')
        return epn.string_value
    except ExperimentParameter.DoesNotExist:
        raise SyncManagerInvalidUIDError()

