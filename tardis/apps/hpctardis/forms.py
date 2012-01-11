from django import forms
from tardis.apps.hpctardis.models import ActivityRecord
from tardis.apps.hpctardis.models import PartyRecord

class ActivitiesSelectForm(forms.Form):
    activities = forms.ModelMultipleChoiceField(queryset=ActivityRecord.objects.all())
    
    
class CollectionPartyRelation(forms.Form):    
     relation = forms.ChoiceField(choices=[('hasCollector','hasCollector: has been aggregated by the related party'),
                                          ('isManagedBy','isManagedBy: is maintained and made accessible by the related party (includes custodian role)'),
                                          ('isOwnedBy ','isOwnedBy: legally belongs to the related party'),
                                          ('isEnrichedBy ','isEnrichedBy: additional value provided to a collection by a party')])
     party = forms.ModelChoiceField(required=False,queryset=PartyRecord.objects.all())
  