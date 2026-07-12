from __future__ import annotations

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from dealio.apps.courses.repositories.logic import CourseLogicRepository
from dealio.apps.common.helpers.decorators.rate_limit import rate_limit
from dealio.apps.pages.repositories.logic import PageLogicRepository
from dealio.apps.pages.web.forms import ContactMessageTemplateForm
from dealio.apps.pages.web.presenters import PageWebErrorPresenter
from dealio.apps.pages.vo.page_vo import (
    PageWebContextKeyVO,
    PageWebReverseNameVO,
    PageWebTemplateVO,
    PageWebValidationMessageVO,
)


class HomePageView(TemplateView):
    template_name = PageWebTemplateVO.HOME.value
    course_logic_repository_class = CourseLogicRepository

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_logic = self.course_logic_repository_class()
        page_logic = PageLogicRepository()
        context.update(
            {
                PageWebContextKeyVO.FEATURED_COURSES.value: course_logic.list_home_featured_courses(),
                PageWebContextKeyVO.FEATURED_ROADMAPS.value: course_logic.list_home_featured_roadmaps(),
                PageWebContextKeyVO.TESTIMONIALS.value: page_logic.list_home_testimonials(),
                PageWebContextKeyVO.FREQUENTLY_ASKED_QUESTIONS.value: page_logic.list_home_frequently_asked_questions(),
            }
        )
        return context


class AboutUsPageView(TemplateView):
    template_name = PageWebTemplateVO.ABOUT_US.value


class ChannelsPageView(TemplateView):
    template_name = PageWebTemplateVO.CHANNELS.value
    page_logic_repository_class = PageLogicRepository

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[PageWebContextKeyVO.CHANNEL_LINKS.value] = self.page_logic_repository_class().list_channel_links()
        return context


@method_decorator(rate_limit(authenticated_limit=5, anonymous_limit=5, period=3600), name="post")
class ContactUsPageView(FormView):
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
