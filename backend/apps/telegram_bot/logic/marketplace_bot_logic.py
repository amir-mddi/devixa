"""Bot-facing marketplace use cases; Telegram is only a delivery adapter."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from urllib.parse import urlsplit, urlunsplit

from django.core.exceptions import PermissionDenied, ValidationError

from backend.apps.marketplace.logic.usecases import MarketplaceUseCases
from backend.apps.marketplace.repositories.marketplace import MarketplaceRepository
from backend.apps.marketplace.value_objects.text import MarketplaceText
from backend.apps.telegram_bot.vo.marketplace_vo import MarketplaceBotCallbackVO as C, MarketplaceBotMessageVO


@dataclass(frozen=True)
class MarketplaceBotScreenDTO:
    text: str
    keyboard: dict | None = None


class MarketplaceBotLogic:
    def __init__(self, repository=None, usecases=None):
        self.repository = repository or MarketplaceRepository()
        self.usecases = usecases or MarketplaceUseCases(repository=self.repository)

    @staticmethod
    def _texts(language):
        return MarketplaceBotMessageVO.CONTENT.get(language, MarketplaceBotMessageVO.CONTENT["en"])

    @staticmethod
    def _button(label, callback):
        return {"text": label, "callback_data": callback}

    @classmethod
    def _screen(cls, text, rows=None):
        return MarketplaceBotScreenDTO(text=text, keyboard={"inline_keyboard": rows} if rows else None)

    @staticmethod
    def _origin(app_url):
        try:
            parts = urlsplit((app_url or "").strip())
            if parts.scheme == "https" and parts.hostname and not parts.username and not parts.password:
                return urlunsplit(("https", parts.netloc, "", "", ""))
        except ValueError:
            pass
        return ""

    def menu(self, language):
        t = self._texts(language)
        return self._screen(t["title"], [
            [self._button(t["mentors"], C.MENTORS)],
            [self._button(t["collaborations"], C.COLLABORATIONS)],
            [self._button(t["workspace"], C.WORKSPACE)],
        ])

    def mentors(self, language):
        t = self._texts(language)
        offers = list(self.repository.public_offers()[:8])
        rows = [[self._button(offer.title[:65], C.OFFER + str(offer.pk))] for offer in offers]
        rows.append([self._button(t["back"], C.MENU)])
        return self._screen(t["mentors"] if offers else t["empty"], rows)

    def offer(self, language, offer_id):
        t = self._texts(language)
        offer = self.repository.get_public_offer(offer_id)
        if not offer:
            return self._screen(t["unavailable"], [[self._button(t["back"], C.MENTORS)]])
        text = "\n".join([
            escape(offer.title), escape(offer.description[:900]),
            escape(offer.subject) + " · " + escape(str(offer.hourly_price)) + " " + t["price"],
            t["schedule"],
        ])
        slots = list(self.repository.available_slots(offer)[:6])
        rows = []
        for slot in slots:
            label = slot.starts_at.strftime("%Y/%m/%d %H:%M")
            rows.append([self._button(t["book"] + " · " + label, C.BOOK + str(slot.pk))])
        if not slots:
            text += "\n" + t["empty"]
        rows.append([self._button(t["back"], C.MENTORS)])
        return self._screen(text, rows)

    def book(self, language, slot_id, user):
        t = self._texts(language)
        if user is None:
            text = t["link_account"]
        else:
            try:
                self.usecases.book(user, slot_id)
            except (ValidationError, PermissionDenied):
                text = t["unavailable"]
            else:
                text = t["booked"]
        return self._screen(text, [[self._button(t["back"], C.MENTORS)]])

    def collaborations(self, language, app_url):
        t = self._texts(language)
        projects = list(self.repository.public_collaborations()[:8])
        rows = []
        lines = [t["collaborations"]] if projects else [t["empty"]]
        for project in projects:
            lines.append("\n" + escape(project.title) + " · " + escape(project.specialty))
            rows.append([self._button(project.title[:65], C.PROJECT + str(project.pk))])
        rows.append([self._button(t["back"], C.MENU)])
        return self._screen("\n".join(lines), rows)

    def collaboration_detail(self, language, project_id, app_url):
        t = self._texts(language)
        project = self.repository.get_public_collaboration(project_id)
        if project is None:
            return self._screen(t["unavailable"], [[self._button(t["back"], C.COLLABORATIONS)]])
        text = "\n".join([escape(project.title), escape(project.specialty), escape(project.description[:1400])])
        rows = []
        origin = self._origin(app_url)
        if origin:
            rows.append([{"text": t["join_project"], "url": origin + "/collaborations/" + str(project.pk) + "/"}])
        rows.append([self._button(t["back"], C.COLLABORATIONS)])
        return self._screen(text, rows)

    def workspace(self, language, user, app_url):
        t = self._texts(language)
        if user is None:
            return self._screen(t["link_account"], [[self._button(t["back"], C.MENU)]])
        bookings = list(self.repository.my_bookings(user)[:8])
        projects = list(self.repository.my_collaborations(user)[:8])
        requests = list(self.repository.my_collaboration_requests(user)[:8])
        lines = [t["workspace"], t["bookings"]]
        lines.extend(escape(item.slot.offer.title) + " · " + escape(item.get_status_display()) for item in bookings)
        if not bookings:
            lines.append(t["no_bookings"])
        lines.append(t["my_projects"])
        lines.extend(escape(item.title) + " · " + escape(item.get_status_display()) for item in projects)
        lines.append(t["my_requests"])
        lines.extend(escape(item.project.title) + " · " + escape(item.get_status_display()) for item in requests)
        rows = []
        origin = self._origin(app_url)
        if origin:
            rows.append([{"text": t["open_site"], "url": origin + "/my-marketplace/"}])
        rows.append([self._button(t["back"], C.MENU)])
        return self._screen("\n".join(lines), rows)
