from tardis.tardis_portal.models import Experiment

from .managers import PublicationManager


class Publication(Experiment):
    """
    Publication records are just experiment records with some metadata, so they
    can be represented by the Experiment model.  However, it is useful to have
    a publication-specific manager, so we can retrieve publication records with
    Publication.safe.draft_publications(user)
    """
    safe = PublicationManager()  # The acl-aware specific manager.
    class Meta:
        # Don't create a database table for this model:
        proxy = True
        auto_created = True
