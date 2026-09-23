from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from .forms import (AcademyForm, AcademyPhotoForm, ApplicationForm, CollaborationProjectForm, CollaborationRequestForm, MentorProfileForm, MentorshipOfferForm,
                    OpportunityForm, ReviewForm, SlotForm)
from .logic.usecases import MarketplaceUseCases
from .repositories.marketplace import MarketplaceRepository
from .value_objects.text import MarketplaceText


repo = MarketplaceRepository()
logic = MarketplaceUseCases()


def _page(request, template, **context):
    return render(request, f"web/marketplace/{template}.html", context)


def mentors(request):
    return _page(request, "mentors", mentors=repo.public_mentors(request.GET.get("q", "")[:100], request.GET.get("city", "")[:100]), offers=repo.public_offers(subject=request.GET.get("subject", "")[:100], city=request.GET.get("city", "")[:100], mode=request.GET.get("mode", "")[:10], maximum_price=request.GET.get("price", "")[:15]))


def mentor_detail(request, pk):
    mentor = repo.get_public_mentor(pk)
    if mentor is None:
        raise Http404
    return _page(request, "mentor_detail", mentor=mentor, offers=repo.profile_offers(mentor), reviews=repo.public_reviews(mentor))


def offer_detail(request, pk):
    offer = repo.get_public_offer(pk)
    if offer is None:
        raise Http404
    return _page(request, "offer_detail", offer=offer, slots=repo.available_slots(offer))


@login_required
def edit_mentor(request):
    profile = repo.get_mentor_for_owner(request.user)
    form = MentorProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        logic.save_profile(request.user, form.cleaned_data)
        messages.success(request, MarketplaceText.PROFILE_SAVED)
        return redirect("marketplace:dashboard")
    return _page(request, "form", form=form, heading=MarketplaceText.MENTOR_PROFILE_HEADING, submit_label=MarketplaceText.MENTOR_PROFILE_SUBMIT)


@login_required
def resume_download(request):
    profile = repo.get_mentor_for_owner(request.user)
    if profile is None or not profile.resume:
        raise Http404
    return FileResponse(profile.resume.open("rb"), as_attachment=True, filename="resume.pdf", content_type="application/pdf")


@login_required
def new_offer(request):
    if repo.get_mentor_for_owner(request.user) is None:
        return redirect("marketplace:mentor_edit")
    form = MentorshipOfferForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        logic.save_offer(request.user, form.cleaned_data)
        messages.success(request, MarketplaceText.OFFER_SAVED)
        return redirect("marketplace:dashboard")
    return _page(request, "form", form=form, heading=MarketplaceText.OFFER_HEADING, submit_label=MarketplaceText.OFFER_SUBMIT)


@login_required
def edit_offer(request, offer_id):
    offer = repo.get_offer_for_owner(offer_id, request.user)
    if offer is None:
        raise Http404
    form = MentorshipOfferForm(request.POST or None, instance=offer)
    if request.method == "POST" and form.is_valid():
        logic.update_offer(request.user, offer, form.cleaned_data)
        messages.success(request, MarketplaceText.OFFER_SAVED)
        return redirect("marketplace:dashboard")
    return _page(request, "form", form=form, heading=MarketplaceText.OFFER_EDIT_HEADING, submit_label=MarketplaceText.OFFER_SUBMIT)


@login_required
def new_slot(request, offer_id):
    offer = repo.get_offer_for_owner(offer_id, request.user)
    if offer is None:
        raise Http404
    form = SlotForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            logic.add_slot(request.user, offer, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, MarketplaceText.SLOT_SAVED)
            return redirect("marketplace:dashboard")
    return _page(request, "form", form=form, heading=MarketplaceText.SLOT_HEADING, submit_label=MarketplaceText.SLOT_SUBMIT)


@login_required
@require_POST
def book_slot(request, slot_id):
    try:
        logic.book(request.user, slot_id)
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    else:
        messages.success(request, MarketplaceText.BOOKED)
    return redirect("marketplace:dashboard")


@login_required
@require_POST
def booking_action(request, booking_id, action):
    booking = repo.get_booking(booking_id)
    if booking is None:
        raise Http404
    if action not in {"confirm", "cancel", "complete"}:
        raise Http404
    try:
        logic.transition_booking(request.user, booking, action)
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    else:
        messages.success(request, MarketplaceText.BOOKING_UPDATED)
    return redirect("marketplace:dashboard")


def academies(request):
    return _page(request, "academies", academies=repo.public_academies(request.GET.get("q", "")[:100], request.GET.get("city", "")[:100]))


def academy_detail(request, pk):
    academy = repo.get_public_academy(pk)
    if academy is None:
        raise Http404
    return _page(request, "academy_detail", academy=academy, opportunities=repo.academy_opportunities(academy), photos=repo.public_academy_photos(academy))


@login_required
def new_academy(request):
    form = AcademyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        logic.save_academy(request.user, form.cleaned_data)
        messages.success(request, MarketplaceText.ACADEMY_SAVED)
        return redirect("marketplace:dashboard")
    return _page(request, "form", form=form, heading=MarketplaceText.ACADEMY_HEADING, submit_label=MarketplaceText.ACADEMY_SUBMIT)


@login_required
def edit_academy(request, academy_id):
    academy = repo.get_owned_academy(academy_id, request.user)
    if academy is None:
        raise Http404
    form = AcademyForm(request.POST or None, instance=academy)
    if request.method == "POST" and form.is_valid():
        logic.update_academy(request.user, academy, form.cleaned_data)
        messages.success(request, MarketplaceText.ACADEMY_SAVED)
        return redirect("marketplace:dashboard")
    return _page(request, "form", form=form, heading=MarketplaceText.ACADEMY_EDIT_HEADING, submit_label=MarketplaceText.ACADEMY_SUBMIT)


def opportunities(request):
    return _page(request, "opportunities", opportunities=repo.public_opportunities(request.GET.get("q", "")[:100], request.GET.get("city", "")[:100], request.GET.get("kind", "")[:12]))


def opportunity_detail(request, pk):
    opportunity = repo.get_public_opportunity(pk)
    if opportunity is None:
        raise Http404
    return _page(request, "opportunity_detail", opportunity=opportunity, form=ApplicationForm())


@login_required
def new_opportunity(request, academy_id):
    academy = repo.get_owned_academy(academy_id, request.user)
    if academy is None:
        raise Http404
    form = OpportunityForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        logic.save_opportunity(request.user, academy, form.cleaned_data)
        messages.success(request, MarketplaceText.OPPORTUNITY_SAVED)
        return redirect("marketplace:dashboard")
    return _page(request, "form", form=form, heading=MarketplaceText.OPPORTUNITY_HEADING, submit_label=MarketplaceText.OPPORTUNITY_SUBMIT)


@login_required
@require_POST
def apply(request, pk):
    opportunity = repo.get_public_opportunity(pk)
    if opportunity is None:
        raise Http404
    form = ApplicationForm(request.POST)
    if form.is_valid():
        application, created = logic.apply(request.user, opportunity, **form.cleaned_data)
        if created:
            messages.success(request, MarketplaceText.APPLIED)
    else:
        messages.error(request, form.errors.as_text())
    return redirect("marketplace:opportunity_detail", pk=pk)


@login_required
def review_booking(request, booking_id):
    booking = repo.get_completed_student_booking(booking_id, request.user)
    if booking is None:
        raise Http404
    form = ReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            logic.review(request.user, booking, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, MarketplaceText.REVIEWED)
            return redirect("marketplace:dashboard")
    return _page(request, "form", form=form, heading=MarketplaceText.REVIEW_HEADING, submit_label=MarketplaceText.REVIEW_SUBMIT)


@login_required
def dashboard(request):
    return _page(
        request, "dashboard",
        profile=repo.get_mentor_for_owner(request.user),
        offers=repo.mine_offers(request.user),
        academies=repo.mine_academies(request.user),
        bookings=repo.my_bookings(request.user),
        applications=repo.academy_applications(request.user),
        my_applications=repo.my_applications(request.user),
        collaboration_projects=repo.my_collaborations(request.user),
        collaboration_inbox=repo.collaboration_inbox(request.user),
        collaboration_sent=repo.my_collaboration_requests(request.user),
    )


@login_required
def add_academy_photo(request, academy_id):
    academy = repo.get_owned_academy(academy_id, request.user)
    if academy is None:
        raise Http404
    form = AcademyPhotoForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            logic.add_academy_photo(request.user, academy, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, MarketplaceText.PHOTO_SAVED)
            return redirect("marketplace:dashboard")
    return _page(request, "form", form=form, heading=MarketplaceText.PHOTO_HEADING, submit_label=MarketplaceText.PHOTO_SUBMIT)


@staff_member_required
def staff_resume_download(request, mentor_id):
    profile = repo.get_mentor_for_id(mentor_id)
    if profile is None or not profile.resume:
        raise Http404
    return FileResponse(profile.resume.open("rb"), as_attachment=True, filename="resume.pdf", content_type="application/pdf")


@login_required
def application_resume_download(request, application_id):
    """Only the receiving academy owner, with the applicant's explicit consent."""
    application = repo.authorized_application_resume(application_id, request.user)
    if application is None:
        raise Http404
    profile = repo.get_mentor_for_owner(application.applicant)
    if profile is None or not profile.resume:
        raise Http404
    return FileResponse(
        profile.resume.open("rb"), as_attachment=True, filename="resume.pdf",
        content_type="application/pdf",
    )


@login_required
@require_POST
def revoke_resume_access(request, application_id):
    logic.revoke_resume_access(request.user, application_id)
    messages.success(request, MarketplaceText.RESUME_ACCESS_REVOKED)
    return redirect("marketplace:dashboard")


def collaborations(request):
    return _page(request, "collaborations", projects=repo.public_collaborations(request.GET.get("q", "")[:100]))


def collaboration_detail(request, pk):
    project = repo.get_public_collaboration(pk)
    if project is None:
        raise Http404
    return _page(request, "collaboration_detail", project=project)


@login_required
def collaboration_new(request):
    form = CollaborationProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        logic.create_collaboration(request.user, form.cleaned_data)
        messages.success(request, MarketplaceText.COLLAB_SAVED)
        return redirect("marketplace:dashboard")
    return _page(request, "form", form=form, heading=MarketplaceText.COLLAB_PROJECT_HEADING, submit_label=MarketplaceText.COLLAB_PROJECT_SUBMIT)


@login_required
def collaboration_apply(request, pk):
    project = repo.get_public_collaboration(pk)
    if project is None:
        raise Http404
    form = CollaborationRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            logic.request_collaboration(request.user, pk, form.cleaned_data["message"])
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, MarketplaceText.COLLAB_REQUEST_SENT)
            return redirect("marketplace:dashboard")
    return _page(request, "form", form=form, heading=MarketplaceText.COLLAB_REQUEST_HEADING, submit_label=MarketplaceText.COLLAB_REQUEST_SUBMIT)


@login_required
@require_POST
def collaboration_decide(request, pk, decision):
    if decision not in {"accepted", "rejected"}:
        raise Http404
    try:
        logic.decide_collaboration_request(request.user, pk, decision)
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    except PermissionDenied:
        raise Http404
    else:
        messages.success(request, MarketplaceText.COLLAB_REQUEST_UPDATED)
    return redirect("marketplace:dashboard")
