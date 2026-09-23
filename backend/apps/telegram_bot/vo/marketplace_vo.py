"""All bot-facing marketplace strings and public route constants."""
from enum import Enum


class MarketplaceBotSection(str, Enum):
    HOME = "marketplace"
    MENTORS = "mentors"
    COLLABORATIONS = "collaborations"
    WORKSPACE = "workspace"


class MarketplaceBotCallbackVO:
    MENU = "mp:menu"
    MENTORS = "mp:mentors"
    OFFER = "mp:offer:"
    PROJECT = "mp:project:"
    BOOK = "mp:book:"
    COLLABORATIONS = "mp:collaborations"
    WORKSPACE = "mp:workspace"
    PREFIX = "mp:"


class MarketplaceBotMessageVO:
    COMMAND = "/marketplace"
    CONTENT = {
        "fa": {
            "title": "خدمات آموزشی دویکسا",
            "mentors": "جلسات منتورینگ",
            "collaborations": "طرح‌های همکاری آموزشی",
            "workspace": "میزکار من",
            "empty": "هنوز مورد منتشرشده‌ای ثبت نشده است.",
            "back": "بازگشت",
            "offer": "جزئیات و زمان‌های جلسه",
            "book": "درخواست جلسه",
            "booked": "درخواست جلسه ثبت شد و منتظر تأیید مدرس است. پرداختی انجام نشده است.",
            "unavailable": "این مورد دیگر در دسترس نیست.",
            "link_account": "برای رزرو یا مشاهده میزکار، حساب سایت خود را به ربات متصل کنید: /link",
            "no_bookings": "هنوز جلسه‌ای رزرو نکرده‌اید.",
            "bookings": "جلسات من:",
            "my_projects": "طرح‌های همکاری من:",
            "my_requests": "درخواست‌های همکاری من:",
            "join_project": "جزئیات و ثبت درخواست در سایت",
            "open_site": "مشاهده و ارسال درخواست در سایت",
            "online": "آنلاین",
            "max_members": "حداکثر اعضا",
            "schedule": "زمان‌های قابل رزرو:",
            "owner": "ثبت‌کننده",
            "price": "تومان / ساعت",
        },
        "en": {
            "title": "Devixa educational marketplace",
            "mentors": "Mentoring sessions",
            "collaborations": "Educational collaborations",
            "workspace": "My workspace",
            "empty": "No published entries yet.",
            "back": "Back",
            "offer": "Details and available slots",
            "book": "Request session",
            "booked": "Session requested; awaiting mentor confirmation. No payment has been made.",
            "unavailable": "This item is no longer available.",
            "link_account": "Link your website account to book or use your workspace: /link",
            "no_bookings": "You have no booked sessions yet.",
            "bookings": "My sessions:",
            "my_projects": "My collaboration projects:",
            "my_requests": "My collaboration requests:",
            "join_project": "Details and application on website",
            "open_site": "View and apply on website",
            "online": "Online",
            "max_members": "Maximum members",
            "schedule": "Available times:",
            "owner": "Posted by",
            "price": "toman / hour",
        },
    }
