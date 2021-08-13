from django.views.generic.base import TemplateView

from tardis.tardis_portal.models import Experiment
from tardis.tardis_portal.shortcuts import render_response_index


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, request, **kwargs):
        c = super().get_context_data(**kwargs)
        limit = 8
        if request.user.is_authenticated:
            private_experiments = Experiment.safe.owned_and_shared(
                    request.user).order_by('-update_time')[:limit]
            c["private_experiments"] = private_experiments
            if len(private_experiments) > 4:
                limit = 4
        public_experiments = Experiment.objects.exclude(
            public_access=Experiment.PUBLIC_ACCESS_NONE).exclude(
            public_access=Experiment.PUBLIC_ACCESS_EMBARGO).order_by(
            '-update_time')[:limit]
        c["public_experiments"] = public_experiments
        c["exps_expand_accordion"] = 1

        return c

    def get(self, request, *args, **kwargs):
        c = self.get_context_data(request, **kwargs)
        return render_response_index(request, self.template_name, c)
