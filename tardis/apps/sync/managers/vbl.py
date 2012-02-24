from django.conf import settings
from suds.client import Client, WebFault
import json
from datetime import datetime
import logging

from tardis.tardis_portal.models import ExperimentParameter
from default_manager import SyncManager
from tardis.apps.sync import TransferService


logger = logging.getLogger(__file__)


class VBLSyncManager(SyncManager):
    def __init__(self, institution='AS'):
        super(VBLSyncManager, self).__init__(institution)

    def _start_file_transfer(self, exp, opts, dest_path):
        epn = _get_epn_from_exp(exp)

        client = Client(settings.VBLSTORAGEGATEWAY, cache=None)

        x509 = opts['password']

        # build destination path
        dirname = os.path.abspath(
            os.path.join(opts['serversite'],  dest_path)
            )
        logger.debug('destination url:  %s' % opts['sl'])
        logger.debug('destination path: %s' % dirname)

        # contact VBL
        key = client.service.VBLstartTransferGridFTP(
            opts['user'],
            x509,
            epn,
            '/Frames\\r\\nTARDIS\\r\\n',
            opts['sl'],
            dirname,
            opts['optionFast'],
            opts['optionPenable'],
            opts['optionP'],
            opts['optionBSenable'],
            opts['optionBS'],
            opts['optionTCPBenable'],
            opts['optionTCPBS'])

        if key.startswith('Error:'):
            logger.error('[vbl] %s: epn %s' % (key, epn))
            raise TransferService.TransferError(key)
        else:
            logger.info('[vbl] %s: pn %s' % (key, epn))

    def _get_status(self, exp):
        epn = _get_epn_from_exp(exp)

        try:
            # Switch the suds cache off, otherwise suds will try to
            # create a tmp directory in /tmp. If it already exists but
            # has the wrong permissions, the authentication will fail.
            client = Client(settings.VBLTARDISINTERFACE, cache=None)
        except WebFault as detail:
            logger.error('VBLTARDISINTERFACE SOAP error: %s' % detail)
            raise TransferService.TransferError('VBL error: %s' % detail)

        result = str(client.service.VBLgetTransferStatus(epn))
        try:
            result_dict = json.loads(result)
        except ValueError:
            logger.warning('VBLgetTransferStatus returned invalid JSON: %s' % result)
            result_dict = None
            raise TransferService.TransferError('VBL error: %s' % result)
        return result_dict


def _get_epn_from_exp(exp):
    try:
        # get EPN (needed to kick-off vbl gridftp transfer)
        epn = ExperimentParameter.objects.get(parameterset__experiment=exp,
                                              name__name='EPN')
        return epn.string_value
    except ExperimentParameter.DoesNotExist:
        raise TransferService.InvalidUIDError('Experiment does not exist')

