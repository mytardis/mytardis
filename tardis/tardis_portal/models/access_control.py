from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth.models import Permission

from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.functional import lazy


class UserProfile(models.Model):
    """
    UserProfile class is an extension to the Django standard user model.

    :attribute isDjangoAccount: is the user a local DB user
    :attribute user: a foreign key to the
       :class:`django.contrib.auth.models.User`
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # This flag will tell us if the main User account was created using any
    # non localdb auth methods. For example, if a first time user authenticates
    # to the system using the ldap auth method, an account will be created for
    # him, say "ldap_user001" and the field isDjangoAccount will be set to
    # False.
    isDjangoAccount = models.BooleanField(
        null=False, blank=False, default=True)

    # This field is supplied by AAF's Rapid Connect service.
    rapidConnectEduPersonTargetedID = models.CharField(
        max_length=400, null=True, blank=True)

    class Meta:
        app_label = 'tardis_portal'

    def __str__(self):
        return self.user.username

    def getUserAuthentications(self):
        return self.userAuthentication_set.all()

    def isValidPublicContact(self):
        '''
        Checks if there's enough information on the user for it to be used as
        a public contact.

        Note: Last name can't be required, because people don't necessarilly
        have a last (or family) name.
        '''
        required_fields = ['email', 'first_name']
        return all(map(lambda f: bool(getattr(self.user, f)), required_fields))

    @property
    def ext_groups(self):

        from ..auth import fix_circular

        if not hasattr(self, '_cached_groups'):
            self._cached_groups = fix_circular.getGroups(self.user)
        return self._cached_groups


@receiver(post_save, sender=User, dispatch_uid="create_user_profile")
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile(user=instance).save()


class GroupAdmin(models.Model):
    """GroupAdmin links the Django User and Group tables for group
    administrators

    :attribute user: a forign key to the
       :class:`django.contrib.auth.models.User`
    :attribute group: a forign key to the
       :class:`django.contrib.auth.models.Group`
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        app_label = 'tardis_portal'

    def __str__(self):
        return '%s: %s' % (self.user.username, self.group.name)


def get_auth_method_choices():
    auth_methods = ()
    for auth_method in settings.AUTH_PROVIDERS:
        auth_methods += ((auth_method[0], auth_method[1]),)
    return auth_methods


# TODO: Generalise auth methods
class UserAuthentication(models.Model):
    userProfile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    username = models.CharField(max_length=50)
    authenticationMethod = models.CharField(
        max_length=30,
        choices=lazy(get_auth_method_choices, tuple)())
    approved = models.BooleanField(default=True)
    __original_approved = None

    class Meta:
        app_label = 'tardis_portal'

    def __init__(self, *args, **kwargs):
        # instantiate comparisonChoices based on settings.AUTH PROVIDERS
        self._comparisonChoicesDict = dict(get_auth_method_choices())

        super().__init__(*args, **kwargs)
        self.__original_approved = self.approved

    def getAuthMethodDescription(self):
        return self._comparisonChoicesDict[self.authenticationMethod]

    def __str__(self):
        return self.username + ' - ' + self.getAuthMethodDescription()

    # pylint: disable=W0222
    def save(self, *args, **kwargs):
        # check if social auth is enabled
        if 'tardis.apps.social_auth' not in settings.INSTALLED_APPS:
            super().save(*args, **kwargs)
            return
        # check if authentication method requires admin approval
        from tardis.apps.social_auth.auth.social_auth import requires_admin_approval
        if not requires_admin_approval(self.authenticationMethod):
            super().save(*args, **kwargs)
            return
        # check if social_auth is enabled
        is_social_auth_enabled = 'tardis.apps.social_auth' in settings.INSTALLED_APPS
        # check if approved status has changed from false to true
        if is_social_auth_enabled and self.approved and not self.__original_approved:
            # get linked user profile
            user_profile = self.userProfile
            user = user_profile.user
            # add user permissions
            user.user_permissions.add(Permission.objects.get(codename='add_experiment'))
            user.user_permissions.add(Permission.objects.get(codename='change_experiment'))
            user.user_permissions.add(Permission.objects.get(codename='change_group'))
            is_openidusermigration_enabled = 'tardis.apps.openid_migration' in settings.INSTALLED_APPS
            if is_openidusermigration_enabled:
                user.user_permissions.add(Permission.objects.get(codename='add_openidusermigration'))
            user.user_permissions.add(Permission.objects.get(codename='change_objectacl'))
            user.user_permissions.add(Permission.objects.get(codename='add_datafile'))
            user.user_permissions.add(Permission.objects.get(codename='change_dataset'))
            # send email to user
            from tardis.apps.social_auth.auth.social_auth import send_account_approved_email
            send_account_approved_email(user.id, self.authenticationMethod)

        super().save(*args, **kwargs)



# this is currently unused, but is the state I would like to reach, ie.
# objects for auth entities, not strings.
# class ObjectPermissions(models.Model):
#     '''
#     Generic object-level permission class.
#     Can relate Users, Groups and other entities to objects of any kind.
#     '''
#     entity_type = models.ForeignKey(ContentType)
#     entity_id = models.PositiveIntegerField()
#     entity_object = GenericForeignKey('entity_type', 'entity_id')
#
#     can_read = models.BooleanField()
#     can_download = models.BooleanField()
#     can_change = models.BooleanField()
#     can_share = models.BooleanField()
#     can_delete = models.BooleanField()
# # or use a char field or enum type that species a verb
#
#     content_type = models.ForeignKey(ContentType)
#     object_id = models.PositiveIntegerField()
#     content_object = GenericForeignKey('content_type', 'object_id')


class ObjectACL(models.Model):
    """The ObjectACL (formerly ExperimentACL) table is the core of the `Tardis
    Authorisation framework
    <http://code.google.com/p/mytardis/wiki/AuthorisationEngineAlt>`_

    :attribute pluginId: the the name of the auth plugin being used
    :attribute entityId: a foreign key to auth plugins
    :attribute object_type: a foreign key to ContentType
    :attribute object_id: the primary key/id of the object_type
    :attribute canRead: gives the user read access
    :attribute canWrite: gives the user write access
    :attribute canDelete: gives the user delete permission
    :attribute isOwner: the experiment owner flag.
    :attribute effectiveDate: the date when access takes into effect
    :attribute expiryDate: the date when access ceases
    :attribute aclOwnershipType: system-owned or user-owned.

    System-owned ACLs will prevent users from removing or
    editing ACL entries to a particular experiment they
    own. User-owned ACLs will allow experiment owners to
    remove/add/edit ACL entries to the experiments they own.

    """

    OWNER_OWNED = 1
    SYSTEM_OWNED = 2
    __COMPARISON_CHOICES = (
        (OWNER_OWNED, 'Owner-owned'),
        (SYSTEM_OWNED, 'System-owned'),
    )

    pluginId = models.CharField(null=False, blank=False, max_length=30)
    entityId = models.CharField(null=False, blank=False, max_length=320)
#    experiment = models.ForeignKey('Experiment')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    canRead = models.BooleanField(default=False)
    canWrite = models.BooleanField(default=False)
    canDelete = models.BooleanField(default=False)
    isOwner = models.BooleanField(default=False)
    effectiveDate = models.DateField(null=True, blank=True)
    expiryDate = models.DateField(null=True, blank=True)
    aclOwnershipType = models.IntegerField(
        choices=__COMPARISON_CHOICES, default=OWNER_OWNED)

    def get_related_object(self):
        """
        If possible, resolve the pluginId/entityId combination to a user or
        group object.
        """
        if self.pluginId == 'django_user':
            return User.objects.get(pk=self.entityId)
        if self.pluginId == 'django_group':
            return Group.objects.get(pk=self.entityId)
        return None

    def get_related_object_group(self):
        """
        If possible, resolve the pluginId/entityId combination to a user or
        group object.
        """
        if self.pluginId == 'django_group':
            return Group.objects.get(pk=self.entityId)
        return None

    def __str__(self):
        return '%s | %i' % (self.content_type.name, self.object_id)

    class Meta:
        app_label = 'tardis_portal'
        ordering = ['content_type', 'object_id']
        verbose_name = "Object ACL"

    @classmethod
    def get_effective_query(cls):
        acl_effective_query = (Q(effectiveDate__lte=datetime.today()) |
                               Q(effectiveDate__isnull=True)) &\
            (Q(expiryDate__gte=datetime.today()) |
             Q(expiryDate__isnull=True))
        return acl_effective_query


def create_user_api_key(sender, **kwargs):
    """
    Auto-create ApiKey objects using Tastypie's create_api_key
    """
    from tastypie.models import create_api_key
    create_api_key(User, **kwargs)


if getattr(settings, 'AUTOGENERATE_API_KEY', False):
    post_save.connect(create_user_api_key, sender=User, weak=False)
