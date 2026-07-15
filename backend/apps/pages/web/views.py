from __future__ import annotations

from django.contrib import messages
from django.shortcuts import redirect
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import RedirectView, TemplateView
from django.views.generic.edit import FormView

from backend.apps.common.helpers.decorators.rate_limit import rate_limit
from backend.apps.common.project_config import get_request_project_context
from backend.apps.common.web.mixins import FormHttpErrorResponseMixin
from backend.apps.common.web.seo.enums.seo_enums import SeoRobotsDirectiveEnum
from backend.apps.common.web.seo.mixins import SeoContextMixin
from backend.apps.courses.repositories.logic import CourseLogicRepository
from backend.apps.pages.repositories.logic import PageLogicRepository
from backend.apps.pages.web.forms import ContactMessageTemplateForm
from backend.apps.pages.web.presenters import PageWebErrorPresenter
from backend.apps.pages.web.seo_presenters import PageSeoPresenter
from backend.apps.pages.vo.page_vo import (
    PageAndroidAppVO,
    PageWebContextKeyVO,
    PageWebReverseNameVO,
    PageWebTemplateVO,
    PageWebValidationMessageVO,
)


class HomePageView(SeoContextMixin, TemplateView):
    template_name = PageWebTemplateVO.HOME.value
    course_logic_repository_class = CourseLogicRepository

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_logic = self.course_logic_repository_class()
        page_logic = PageLogicRepository()
        context.update(
            {
                PageWebContextKeyVO.FEATURED_COURSES.value: (
                    course_logic.list_home_featured_courses()
                ),
                PageWebContextKeyVO.FEATURED_ROADMAPS.value: (
                    course_logic.list_home_featured_roadmaps()
                ),
                PageWebContextKeyVO.TESTIMONIALS.value: page_logic.list_home_testimonials(),
                PageWebContextKeyVO.FREQUENTLY_ASKED_QUESTIONS.value: (
                    page_logic.list_home_frequently_asked_questions()
                ),
            }
        )
        return context


class AboutUsPageView(SeoContextMixin, TemplateView):
    template_name = PageWebTemplateVO.ABOUT_US.value


class ChannelsPageView(SeoContextMixin, TemplateView):
    template_name = PageWebTemplateVO.CHANNELS.value
    page_logic_repository_class = PageLogicRepository

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[PageWebContextKeyVO.CHANNEL_LINKS.value] = (
            self.page_logic_repository_class().list_channel_links()
        )
        return context


@method_decorator(rate_limit(authenticated_limit=5, anonymous_limit=5, period=3600), name="post")
class ContactUsPageView(SeoContextMixin, FormHttpErrorResponseMixin, FormView):
    template_name = PageWebTemplateVO.CONTACT_US.value
    form_class = ContactMessageTemplateForm
    success_url = reverse_lazy(PageWebReverseNameVO.CONTACT_US.value)
    page_logic_repository_class = PageLogicRepository
    error_presenter_class = PageWebErrorPresenter

    def form_valid(self, form):
        result = self.page_logic_repository_class().send_contact_message(dto=form.to_dto())

        if not result.is_success:
            form.add_error(None, self.error_presenter_class.message_for(result.error_code))
            return self.form_invalid(form)

        messages.success(self.request, PageWebValidationMessageVO.CONTACT_MESSAGE_SENT.value)
        return redirect(self.get_success_url())


class AndroidAppPageView(SeoContextMixin, TemplateView):
    template_name = PageWebTemplateVO.ANDROID_APP.value
    seo_presenter_class = PageSeoPresenter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                PageWebContextKeyVO.ANDROID_VERSION.value: PageAndroidAppVO.VERSION.value,
                PageWebContextKeyVO.ANDROID_FILENAME.value: PageAndroidAppVO.APK_FILENAME.value,
            }
        )
        return context

    def get_seo_override(self, context):
        return self.seo_presenter_class().android_app(
            request=self.request,
            project_mapping=get_request_project_context(self.request),
        )


class AndroidAppDownloadView(RedirectView):
    """Redirect a stable public URL to the current versioned APK asset."""

    permanent = False
    query_string = False

    def get_redirect_url(self, *args, **kwargs):
        return static(PageAndroidAppVO.APK_STATIC_PATH.value)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response["X-Robots-Tag"] = SeoRobotsDirectiveEnum.NOINDEX.value
        return response

