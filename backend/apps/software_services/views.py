from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from backend.apps.common.web.seo.mixins import SeoContextMixin
from backend.apps.common.web.seo.dtos.seo_dtos import SeoMetadataOverrideDTO
from django.utils.decorators import method_decorator
from django.views.generic.edit import FormView

from backend.apps.common.helpers.decorators.rate_limit import rate_limit
from backend.apps.software_services.forms import SoftwareProjectRequestForm
from backend.apps.software_services.logic.request_logic import CreateSoftwareRequestLogic
from backend.apps.software_services.value_objects.request_vo import (
    SoftwareRequestMessageVO, SoftwareRequestRouteVO, SoftwareRequestTemplateVO, SoftwareRequestSeoVO,
)


@method_decorator(rate_limit(authenticated_limit=12, anonymous_limit=8, period=3600), name="post")
class SoftwareServicePageView(SeoContextMixin, FormView):
    template_name = SoftwareRequestTemplateVO.LANDING.value
    form_class = SoftwareProjectRequestForm
    success_url = reverse_lazy(SoftwareRequestRouteVO.REVERSE.value)
    logic_class = CreateSoftwareRequestLogic

    def get_seo_override(self, context):
        return SeoMetadataOverrideDTO(
            title=SoftwareRequestSeoVO.TITLE.value,
            description=SoftwareRequestSeoVO.DESCRIPTION.value,
            canonical_path=reverse(SoftwareRequestRouteVO.REVERSE.value),
        )

    def form_valid(self, form):
        customer = self.request.user if self.request.user.is_authenticated else None
        self.logic_class().execute(dto=form.to_dto(), customer=customer)
        messages.success(self.request, SoftwareRequestMessageVO.SENT.value)
        return redirect(self.get_success_url())
