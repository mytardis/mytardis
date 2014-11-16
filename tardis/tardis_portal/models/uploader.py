from django.db import models


class Uploader(models.Model):
    '''
    Represents a PC whose user(s) have expressed interest in 
    uploading to this MyTardis instance - either a PC attached
    to a data-collection instrument, or an end-user's machine.
    The upload method (once approved) could be RSYNC over SSH
    to a staging area.

    Some field values within each uploader record (e.g. IP address)
    may change after this uploader has been approved.  The MyTardis
    admin who does the approving needs to determine whether the
    Uploader's IP range needs to be added to a hosts.allow file or
    to a firewall rule, or whether an SSH key-pair is sufficient.
    '''

    name = models.CharField(max_length=64)
    contact_name = models.CharField(max_length=64)
    contact_email = models.CharField(max_length=64)

    user_agent_name = models.CharField(max_length=64)
    user_agent_version = models.CharField(max_length=32)
    user_agent_install_location = models.CharField(max_length=128)

    os_platform = models.CharField(max_length=64)
    os_system = models.CharField(max_length=64)
    os_release = models.CharField(max_length=32)
    os_version = models.CharField(max_length=32)
    os_username = models.CharField(max_length=64)

    machine = models.CharField(max_length=64)
    architecture = models.CharField(max_length=64)
    processor = models.CharField(max_length=64)
    memory = models.CharField(max_length=32)
    cpus = models.IntegerField()

    disk_usage = models.TextField()
    data_path = models.CharField(max_length=64)
    default_user = models.CharField(max_length=64)

    interface = models.CharField(max_length=64, default="", blank=False) 
    mac_address = models.CharField(max_length=64, unique=True, blank=False) 
    ipv4_address = models.CharField(max_length=16)
    ipv6_address = models.CharField(max_length=64)
    subnet_mask = models.CharField(max_length=16)

    hostname = models.CharField(max_length=64)

    # The wan_ip_address is populated in TastyPie by looking in request.META. It could be IPv4 or IPv6
    wan_ip_address = models.CharField(max_length=64)

    created_time = models.DateTimeField()
    updated_time = models.DateTimeField()

    class Meta:
        app_label = 'tardis_portal'
        verbose_name_plural = 'Uploaders'

    def __unicode__(self):
        return self.name + " | " + self.interface + " | " + self.mac_address


class UploaderStagingHost(models.Model):
    '''
    Represents a file server (usually accessible via RSYNC over SSH)
    which allows "uploaders" to write to MyTardis's staging area.
    '''

    host = models.CharField(default="", max_length=64)  # Could be hostname or IP address

    # What needs to be updated before a new uploader can begin
    # using RSYNC over SSH to upload to this host?
    uses_hosts_allow = models.BooleanField()
    uses_iptables_firewall = models.BooleanField()
    uses_external_firewall = models.BooleanField()

    class Meta:
        app_label = 'tardis_portal'
        verbose_name_plural = 'UploaderStagingHosts'

    def __unicode__(self):
        return self.host


class UploaderRegistrationRequest(models.Model):
    '''
    Represents a request to register a new instrument PC with this
    MyTardis instance and allow it to act as an "uploader".
    The upload method could be RSYNC over SSH to a staging area for example.
    '''

    uploader = models.ForeignKey(Uploader, unique=True)

    requester_name = models.CharField(max_length=64)
    requester_email = models.CharField(max_length=64)
    requester_public_key = models.TextField()
    request_time = models.DateTimeField(null=True, blank=True)

    approved = models.BooleanField()
    approved_staging_host = models.ForeignKey(UploaderStagingHost, null=True, blank=True, default=None)
    approved_username = models.CharField(max_length=32, null=True, blank=True, default=None)
    approver_comments = models.TextField(null=True, blank=True, default=None)
    approval_expiry = models.DateField(null=True, blank=True, default=None)
    approval_time = models.DateTimeField(null=True, blank=True, default=None)

    class Meta:
        app_label = 'tardis_portal'
        verbose_name_plural = 'UploaderRegistrationRequests'

    def __unicode__(self):
        '''
        A single "uploader" (usually an instrument PC) may send multiple
        registration requests for different network interfaces (Ethernet,
        WiFi etc.) with different MAC addresses.

        '''
        return self.uploader.name + " | " + self.uploader.mac_address + " | " + self.requester_name + " | " + str(self.request_time)


