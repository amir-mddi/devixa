from __future__ import annotations


class TelegramBotLanguageVO:
    EN = "en"
    FA = "fa"
    SUPPORTED = {EN, FA}


class TelegramBotCallbackVO:
    MAIN_MENU = "menu:main"
    LINK = "menu:link"
    ACCOUNT = "menu:account"
    VERIFY_EMAIL = "menu:verify_email"
    FORGOT_PASSWORD = "menu:forgot_password"
    CREATE_USER = "menu:create_user"
    WEBAPP = "menu:webapp"
    LANGUAGE = "menu:language"
    LANG_EN = "lang:en"
    LANG_FA = "lang:fa"
    HELP = "menu:help"
    COURSES = "c:l:1"
    MY_COURSES = "e:mine"
    MY_ORDERS = "o:mine"
    REVIEW_QUEUE = "r:q"
    UNLINK_ASK = "menu:unlink_ask"
    UNLINK_CONFIRM = "menu:unlink_confirm"
    CANCEL = "menu:cancel"
    CHANNELS = "menu:channels"


class TelegramBotStateVO:
    LINK_EMAIL = "link_email"
    LINK_CODE = "link_code"
    VERIFY_EMAIL_CODE = "verify_email_code"
    FORGOT_PASSWORD_EMAIL = "forgot_password_email"
    CREATE_USERNAME = "create_user_username"
    CREATE_EMAIL = "create_user_email"
    CREATE_PHONE = "create_user_phone"
    CREATE_FIRST_NAME = "create_user_first_name"
    CREATE_LAST_NAME = "create_user_last_name"
    CREATE_CONFIRM = "create_user_confirm"
    UNLINK_CONFIRM = "unlink_confirm"
    REVIEW_RATING = "course_review_rating"
    REVIEW_TITLE = "course_review_title"
    REVIEW_COMMENT = "course_review_comment"
    COURSE_TITLE = "admin_course_title"
    COURSE_SHORT_DESCRIPTION = "admin_course_short_description"
    COURSE_DESCRIPTION = "admin_course_description"
    COURSE_PRICE = "admin_course_price"
    COURSE_DURATION = "admin_course_duration"
    COURSE_LEVEL = "admin_course_level"
    COURSE_PUBLISH = "admin_course_publish"
    LESSON_TITLE = "admin_lesson_title"
    LESSON_DESCRIPTION = "admin_lesson_description"
    LESSON_CONTENT = "admin_lesson_content"
    LESSON_VIDEO_URL = "admin_lesson_video_url"
    LESSON_DURATION = "admin_lesson_duration"
    LESSON_POSITION = "admin_lesson_position"
    LESSON_PREVIEW = "admin_lesson_preview"


class TelegramBotButtonKeyVO:
    LINK = "link"
    ACCOUNT = "account"
    VERIFY_EMAIL = "verify_email"
    FORGOT_PASSWORD = "forgot_password"
    CREATE_USER = "create_user"
    WEBAPP = "webapp"
    LANGUAGE = "language"
    UNLINK = "unlink"
    HELP = "help"
    COURSES = "courses"
    MY_COURSES = "my_courses"
    MY_ORDERS = "my_orders"
    REVIEW_QUEUE = "review_queue"
    ADMIN_COURSES = "admin_courses"
    CREATE_COURSE = "create_course"
    MAIN_MENU = "main_menu"
    CANCEL = "cancel"
    CHANNELS = "channels"
    YES_UNLINK = "yes_unlink"
    CONFIRM_CREATE = "confirm_create"


class TelegramBotButtonTextVO:
    LANGUAGE_BUTTONS = {
        TelegramBotLanguageVO.EN: "🇬🇧 English",
        TelegramBotLanguageVO.FA: "🇮🇷 فارسی",
    }

    BUTTONS = {
        TelegramBotLanguageVO.EN: {
            TelegramBotButtonKeyVO.LINK: "🔗 Link account",
            TelegramBotButtonKeyVO.ACCOUNT: "👤 My account",
            TelegramBotButtonKeyVO.VERIFY_EMAIL: "✅ Verify email",
            TelegramBotButtonKeyVO.FORGOT_PASSWORD: "🔐 Forgot password",
            TelegramBotButtonKeyVO.CREATE_USER: "➕ Create user",
            TelegramBotButtonKeyVO.WEBAPP: "🌐 Open app",
            TelegramBotButtonKeyVO.LANGUAGE: "🌍 Language",
            TelegramBotButtonKeyVO.UNLINK: "🚪 Unlink",
            TelegramBotButtonKeyVO.HELP: "❓ Help",
            TelegramBotButtonKeyVO.CHANNELS: "📣 Channels",
            TelegramBotButtonKeyVO.COURSES: "📚 Courses",
            TelegramBotButtonKeyVO.MY_COURSES: "🎓 My courses",
            TelegramBotButtonKeyVO.MY_ORDERS: "🧾 My orders",
            TelegramBotButtonKeyVO.REVIEW_QUEUE: "🛡 Review queue",
            TelegramBotButtonKeyVO.ADMIN_COURSES: "🧑‍🏫 Admin courses",
            TelegramBotButtonKeyVO.CREATE_COURSE: "➕ Create course",
            TelegramBotButtonKeyVO.MAIN_MENU: "⬅️ Main menu",
            TelegramBotButtonKeyVO.CANCEL: "Cancel",
            TelegramBotButtonKeyVO.YES_UNLINK: "✅ Yes, unlink",
            TelegramBotButtonKeyVO.CONFIRM_CREATE: "✅ Create user",
        },
        TelegramBotLanguageVO.FA: {
            TelegramBotButtonKeyVO.LINK: "🔗 اتصال حساب",
            TelegramBotButtonKeyVO.ACCOUNT: "👤 حساب من",
            TelegramBotButtonKeyVO.VERIFY_EMAIL: "✅ تأیید ایمیل",
            TelegramBotButtonKeyVO.FORGOT_PASSWORD: "🔐 فراموشی رمز عبور",
            TelegramBotButtonKeyVO.CREATE_USER: "➕ ساخت کاربر",
            TelegramBotButtonKeyVO.WEBAPP: "🌐 باز کردن برنامه",
            TelegramBotButtonKeyVO.LANGUAGE: "🌍 زبان",
            TelegramBotButtonKeyVO.UNLINK: "🚪 قطع اتصال",
            TelegramBotButtonKeyVO.HELP: "❓ راهنما",
            TelegramBotButtonKeyVO.CHANNELS: "📣 کانال‌ها",
            TelegramBotButtonKeyVO.COURSES: "📚 دوره‌ها",
            TelegramBotButtonKeyVO.MY_COURSES: "🎓 دوره‌های من",
            TelegramBotButtonKeyVO.MY_ORDERS: "🧾 سفارش‌های من",
            TelegramBotButtonKeyVO.REVIEW_QUEUE: "🛡 بررسی دیدگاه‌ها",
            TelegramBotButtonKeyVO.ADMIN_COURSES: "🧑‍🏫 مدیریت دوره‌ها",
            TelegramBotButtonKeyVO.CREATE_COURSE: "➕ ساخت دوره",
            TelegramBotButtonKeyVO.MAIN_MENU: "⬅️ منوی اصلی",
            TelegramBotButtonKeyVO.CANCEL: "لغو",
            TelegramBotButtonKeyVO.YES_UNLINK: "✅ بله، قطع اتصال",
            TelegramBotButtonKeyVO.CONFIRM_CREATE: "✅ ساخت کاربر",
        },
    }


class TelegramBotAliasVO:
    LANGUAGE_EN_ALIASES = {"english", "en"}
    LANGUAGE_FA_ALIASES = {"فارسی", "farsi", "fa", "persian"}
    CANCEL_ALIASES = {"cancel", "لغو"}
    MAIN_MENU_ALIASES = {"main menu", "menu", "منوی اصلی"}
    YES_UNLINK_ALIASES = {"yes unlink", "yes", "unlink", "بله حذف اتصال", "بله قطع اتصال"}
    CREATE_CONFIRM_ALIASES = {"create user", "create", "yes create", "confirm", "تایید", "ساخت کاربر"}
    YES_ALIASES = {"yes", "y", "true", "1", "publish", "preview", "بله", "آره", "اره", "بلی"}
    NO_ALIASES = {"no", "n", "false", "0", "draft", "نه", "خیر"}
    MENU_BUTTON_ALIASES = {
        TelegramBotButtonKeyVO.LINK: {"link account", "اتصال حساب"},
        TelegramBotButtonKeyVO.ACCOUNT: {"my account", "account", "حساب من"},
        TelegramBotButtonKeyVO.VERIFY_EMAIL: {"verify email", "email verification", "تایید ایمیل", "تأیید ایمیل"},
        TelegramBotButtonKeyVO.FORGOT_PASSWORD: {"forgot password", "فراموشی رمز عبور"},
        TelegramBotButtonKeyVO.CREATE_USER: {"create user", "ساخت کاربر"},
        TelegramBotButtonKeyVO.WEBAPP: {"open app", "web app", "باز کردن برنامه"},
        TelegramBotButtonKeyVO.LANGUAGE: {"language", "زبان"},
        TelegramBotButtonKeyVO.UNLINK: {"unlink", "قطع اتصال"},
        TelegramBotButtonKeyVO.HELP: {"help", "راهنما"},
        TelegramBotButtonKeyVO.CHANNELS: {"channels", "channel", "کانال", "کانال‌ها", "کانال ها"},
        TelegramBotButtonKeyVO.COURSES: {"courses", "course", "دوره", "دوره‌ها", "دوره ها"},
        TelegramBotButtonKeyVO.MY_COURSES: {"my courses", "my course", "دوره‌های من", "دوره های من"},
        TelegramBotButtonKeyVO.MY_ORDERS: {"my orders", "orders", "سفارش‌های من", "سفارش های من"},
        TelegramBotButtonKeyVO.REVIEW_QUEUE: {"review queue", "reviews queue", "بررسی دیدگاه‌ها", "بررسی دیدگاه ها"},
        TelegramBotButtonKeyVO.ADMIN_COURSES: {"admin courses", "manage courses", "course admin", "مدیریت دوره‌ها", "مدیریت دوره ها"},
        TelegramBotButtonKeyVO.CREATE_COURSE: {"create course", "new course", "ساخت دوره", "دوره جدید"},
    }


class TelegramBotMessageTextVO:
    DEFAULT_USER_NAME = {
        TelegramBotLanguageVO.EN: "there",
        TelegramBotLanguageVO.FA: "کاربر",
    }
    LINK_EMAIL_SUBJECT = {
        TelegramBotLanguageVO.EN: "Telegram account link code",
        TelegramBotLanguageVO.FA: "کد اتصال حساب تلگرام",
    }

    TEXTS = {
        TelegramBotLanguageVO.EN: {
            "choose_language": "Please choose your language / لطفاً زبان خود را انتخاب کنید:",
            "language_saved": "Language saved. Choose an action:",
            "canceled": "Canceled.",
            "use_buttons": "Please use the menu buttons below.",
            "unknown": "Unknown action. Use the buttons below.",
            "channels_title": "Join our official channels:",
            "channels_not_configured": "Channel links are not configured yet.",
            "telegram_channel": "Telegram channel",
            "bale_channel": "Bale channel",
            "rubika_channel": "Rubika channel",
            "private_only": "Please message me privately to manage your account.",
            "menu_linked": "Welcome back, <b>{name}</b>!\n\nChoose an action:",
            "menu_guest": "Welcome to Devixa bot.\n\nChoose an action:",
            "not_linked": "Your account is not linked yet. Tap <b>Link account</b> below.",
            "already_linked": "Your Telegram account is already linked.",
            "link_prompt": "Send your app account email address here.\n\nExample: <code>you@example.com</code>",
            "invalid_email": "That does not look like a valid email. Please send only your email address.",
            "link_code_sent": "If this email exists, I sent a 6-digit link code to it.\n\nNow send the 6-digit code here.",
            "code_only": "Please send the 6-digit code only. Example: <code>123456</code>",
            "invalid_link_code": "Invalid or expired link code. Try again, or cancel and request a new code.",
            "linked_success": "Your Telegram account is linked successfully.",
            "verify_already": "Your email is already verified.",
            "verify_sent": "I sent a 6-digit email verification code to your linked email. Send the code here.",
            "verify_success": "✅ Email verified successfully.",
            "verify_invalid": "Invalid or expired verification code. Try again or request a new code.",
            "forgot_prompt": "Send your account email address, and I will send a password recovery code if it exists.",
            "forgot_sent": "If this account exists, a password recovery code has been sent to the account email.\n\nFor security, do not send your new password in Telegram. Use the app/API reset form with the code.",
            "unlink_ask": "Are you sure you want to unlink this Telegram account?",
            "unlink_choose": "Choose <b>Yes, unlink</b> or <b>Cancel</b> from the keyboard below.",
            "unlinked": "Your Telegram account has been unlinked.",
            "webapp_missing": "Web app URL is not configured yet.",
            "webapp_open": "Open the app here: <a href=\"{url}\">Open app</a>",
            "admin_only": "Only a linked admin can use this Telegram admin action.",
            "admin_courses_empty": "No courses exist yet.",
            "course_create_start": "Create a new course. Send the course title first.",
            "course_short_description_prompt": "Send a short description for the course. Max 300 chars.",
            "course_description_prompt": "Send the full course description, or send <code>-</code> to skip.",
            "course_price_prompt": "Send the course price as a number. Use <code>0</code> for a free course.",
            "course_duration_prompt": "Send total course duration in minutes. Example: <code>120</code>",
            "course_level_prompt": "Send course level: <code>beginner</code>, <code>intermediate</code>, <code>advanced</code>, or <code>all_levels</code>.",
            "course_publish_prompt": "Publish now? Send <code>yes</code> to publish or <code>no</code> to keep it as draft.",
            "course_created": "✅ Course created successfully.",
            "course_status_updated": "✅ Course status updated.",
            "lesson_create_start": "Add a lesson to this course. Send the lesson title first.",
            "lesson_description_prompt": "Send lesson description, or send <code>-</code> to skip.",
            "lesson_content_prompt": "Send lesson content/text, or send <code>-</code> to skip.",
            "lesson_video_url_prompt": "Send video URL, or send <code>-</code> to skip.",
            "lesson_duration_prompt": "Send lesson duration in minutes. Example: <code>15</code>",
            "lesson_position_prompt": "Send lesson position number, or send <code>-</code> to auto-place at the end.",
            "lesson_preview_prompt": "Is this a free preview lesson? Send <code>yes</code> or <code>no</code>.",
            "lesson_created": "✅ Lesson added successfully.",
            "course_login_required": "Please link your account before buying courses, viewing enrollments, or writing reviews.",
            "courses_empty": "No published courses are available yet.",
            "my_courses_empty": "You do not have any active courses yet.",
            "orders_empty": "You do not have any orders yet.",
            "reviews_empty": "No approved reviews yet.",
            "review_rating_prompt": "Send a rating from 1 to 5 for this course.",
            "review_title_prompt": "Optional: send a short review title, or send <code>-</code> to skip.",
            "review_comment_prompt": "Now send your review comment. It will be visible only after admin approval.",
            "review_pending": "✅ Thanks! Your review is waiting for admin approval.",
            "review_queue_empty": "There are no pending reviews.",
            "payment_manual": "✅ Order and manual payment were created. Admin confirmation is required before enrollment.",
            "payment_success": "✅ Payment succeeded. You are now enrolled in the course.",
            "payment_created": "✅ Order/payment created successfully.",
            "course_already_owned": "You already purchased this course.",
            "create_start": "Create a new app user.\n\nSend the username first.\nExample: <code>ali_ahmadi</code>",
            "create_email": "Now send the user Gmail address.\nExample: <code>user@gmail.com</code>",
            "create_phone": "Now send the phone number.\nExample: <code>09123456789</code>",
            "create_first_name": "Now send the first name in Persian.\nExample: <code>علی</code>",
            "create_last_name": "Now send the last name in Persian.\nExample: <code>احمدی</code>",
            "create_choose": "Choose <b>Create user</b> or <b>Cancel</b> from the keyboard below.",
            "create_expired": "The create-user session expired. Send the username again.",
            "create_duplicate": "A user with this username, email, or phone already exists. Start again with new data.",
            "create_done_followup": "I also sent a password setup/recovery code to the user's email. They can use the app forgot-password reset form to set their password.",
            "create_email_failed": "The user was created, but I could not send the password setup email. Use the app/admin panel forgot-password flow to send it again.",
            "link_usage": "Usage: <code>/link your-email@example.com</code>",
            "invalid_username_detail": "Invalid username: {error}\n\nSend the username again.",
            "username_exists": "This username already exists. Send another username.",
            "invalid_create_email_detail": "Invalid email: {error}\n\nSend a Gmail address again.",
            "email_exists": "This email already exists. Send another Gmail address.",
            "invalid_phone_detail": "Invalid phone number: {error}\n\nSend the phone number again.",
            "phone_exists": "This phone number already exists. Send another phone number.",
            "invalid_first_name_detail": "Invalid first name: {error}\n\nSend the first name again.",
            "invalid_last_name_detail": "Invalid last name: {error}\n\nSend the last name again.",
            "create_failed": "Could not create the user: {error}",
            "create_success": "✅ User created successfully.\n\nUsername: <code>{username}</code>\nEmail: <code>{email}</code>\nPhone: <code>{phone}</code>\n\n{follow_up}",
            "create_confirm_text": "Please confirm this new user:\n\nUsername: <code>{username}</code>\nEmail: <code>{email}</code>\nPhone: <code>{phone}</code>\nFirst name: <code>{first_name}</code>\nLast name: <code>{last_name}</code>\n\nNo password will be sent in Telegram. The user will set their password by email reset code.",
            "yes": "yes",
            "no": "no",
            "account_text": "<b>Your account</b>\nUsername: <code>{username}</code>\nFirst name: <code>{first_name}</code>\nLast name: <code>{last_name}</code>\nEmail: <code>{email}</code>\nPhone: <code>{phone}</code>\nEmail verified: <code>{verified}</code>",
            "courses_heading": "<b>📚 Courses</b>",
            "course_list_item": "\n<b>{index}. {title}</b>{rating}\n{description}\nPrice: <code>{price}</code>",
            "view_course_button": "🔎 {title}",
            "prev_button": "⬅️ Prev",
            "next_button": "Next ➡️",
            "main_menu_button": "⬅️ Main menu",
            "course_detail_text": "<b>{title}</b>\n\n{description}\n\nLevel: <code>{level}</code>\nDuration: <code>{duration} min</code>\nLessons: <code>{lessons}</code>\nRating: <code>{rating}</code>\nPrice: <code>{price}</code>",
            "lessons_button": "🧩 Lessons",
            "reviews_button": "⭐ Reviews",
            "buy_button": "🛒 Buy / Enroll",
            "write_review_button": "✍️ Write review",
            "courses_back_button": "⬅️ Courses",
            "course_back_button": "⬅️ Course",
            "lessons_heading": "<b>🧩 {title} lessons</b>",
            "no_lessons": "No lessons are published for this course yet.",
            "lesson_item": "\n{lock} <b>{position}. {title}</b>\nDuration: <code>{duration} min</code>",
            "video_line": "Video: {url}",
            "reviews_heading": "<b>⭐ Approved reviews for {title}</b>",
            "review_item": "\n<b>{rating}/5{title}</b>\nBy: <code>{user}</code>\n{comment}",
            "my_courses_heading": "<b>🎓 My courses</b>",
            "enrollment_item": "\n<b>{title}</b>\nStatus: <code>{status}</code>\nEnrolled: <code>{enrolled_at}</code>",
            "open_course_button": "Open {title}",
            "my_orders_heading": "<b>🧾 My orders</b>",
            "order_item": "\n<b>{order_number}</b>\nCourses: <code>{courses}</code>\nStatus: <code>{status}</code>\nTotal: <code>{total}</code>",
            "review_saved_with_id": "{message}\nReview ID: <code>{review_id}</code>",
            "review_queue_heading": "<b>🛡 Pending course reviews</b>",
            "pending_review_item": "\n<b>{course}</b>\nUser: <code>{user}</code> | Rating: <code>{rating}/5</code>\n{comment}",
            "approve_button": "✅ Approve",
            "reject_button": "❌ Reject",
            "refresh_button": "Refresh",
            "admin_review_note": "Moderated from Telegram bot.",
            "review_moderated": "✅ Review <code>{review_id}</code> marked as <b>{status}</b>.",
            "back_to_queue_button": "Back to queue",
            "payment_my_courses_button": "🎓 My courses",
            "payment_my_orders_button": "🧾 My orders",
            "order_payment_order": "Order: <code>{order_number}</code>",
            "order_payment_status": "Status: <code>{status}</code>",
            "order_payment_total": "Total: <code>{total}</code>",
            "order_payment_payment": "Payment: <code>{payment_number}</code>",
            "order_payment_provider": "Provider: <code>{provider}</code>",
            "order_payment_payment_status": "Payment status: <code>{status}</code>",
            "order_payment_url": "Payment URL: {url}",
            "course_title_invalid": "Course title must be between 3 and 180 characters.",
            "lesson_title_invalid": "Lesson title must be between 2 and 180 characters.",
            "lesson_created_detail": "{message}\n\n<b>{title}</b>\nCourse: <code>{course}</code>\nPosition: <code>{position}</code>",
            "admin_courses_heading": "<b>🧑‍🏫 Admin courses</b>",
            "admin_course_list_item": "\n<b>{index}. {title}</b>\nStatus: <code>{status}</code> | Price: <code>{price}</code>",
            "manage_course_button": "Manage {title}",
            "admin_course_text": "<b>{title}</b>\n\nStatus: <code>{status}</code>\nSlug: <code>{slug}</code>\nLevel: <code>{level}</code>\nDuration: <code>{duration} min</code>\nLessons: <code>{lessons}</code>\nPrice: <code>{price}</code>\n\n{description}",
            "add_lesson_button": "➕ Add lesson",
            "publish_button": "✅ Publish",
            "unpublish_button": "📥 Unpublish",
            "archive_button": "🗄 Archive",
            "public_view_button": "👁 Public view",
            "all_courses_button": "📋 All courses",
            "help_text": "<b>Available actions</b>\nUse the bottom keyboard buttons instead of typing commands.\n\n🔗 <b>Link account</b> - connect your app account\n👤 <b>My account</b> - show linked account\n✅ <b>Verify email</b> - send and confirm email verification code\n🔐 <b>Forgot password</b> - send a recovery code\n➕ <b>Create user</b> - admin only, create an app user\n🌐 <b>Open app</b> - open the configured web app\n🌍 <b>Language</b> - change bot language\n🚪 <b>Unlink</b> - remove the Telegram link",
            "placeholder_language": "Language / زبان",
            "placeholder_main_menu": "Choose an action",
            "placeholder_cancel": "Send the requested value or cancel",
            "placeholder_confirm": "Confirm or cancel",
        },
        TelegramBotLanguageVO.FA: {
            "choose_language": "لطفاً زبان ربات را انتخاب کنید:",
            "language_saved": "زبان ذخیره شد. یک گزینه را انتخاب کنید:",
            "canceled": "لغو شد.",
            "use_buttons": "لطفاً از دکمه‌های پایین استفاده کنید.",
            "unknown": "گزینه نامعتبر است. از دکمه‌های پایین استفاده کنید.",
            "private_only": "لطفاً برای مدیریت حساب، به صورت خصوصی به من پیام بدهید.",
            "menu_linked": "خوش برگشتی، <b>{name}</b>!\n\nیک گزینه را انتخاب کنید:",
            "menu_guest": "به ربات Devixa خوش آمدید.\n\nیک گزینه را انتخاب کنید:",
            "not_linked": "حساب شما هنوز متصل نشده است. دکمه <b>اتصال حساب</b> را بزنید.",
            "already_linked": "حساب تلگرام شما قبلاً متصل شده است.",
            "link_prompt": "ایمیل حساب کاربری خود را ارسال کنید.\n\nمثال: <code>you@example.com</code>",
            "invalid_email": "ایمیل وارد شده معتبر نیست. لطفاً فقط آدرس ایمیل را ارسال کنید.",
            "link_code_sent": "اگر این ایمیل وجود داشته باشد، کد ۶ رقمی اتصال برای آن ارسال شد.\n\nحالا کد ۶ رقمی را همین‌جا بفرستید.",
            "code_only": "لطفاً فقط کد ۶ رقمی را ارسال کنید. مثال: <code>123456</code>",
            "invalid_link_code": "کد اتصال نامعتبر است یا منقضی شده. دوباره تلاش کنید یا لغو کنید و کد جدید بگیرید.",
            "linked_success": "حساب تلگرام شما با موفقیت متصل شد.",
            "verify_already": "ایمیل شما قبلاً تأیید شده است.",
            "verify_sent": "کد ۶ رقمی تأیید ایمیل به ایمیل متصل‌شده ارسال شد. کد را همین‌جا بفرستید.",
            "verify_success": "✅ ایمیل با موفقیت تأیید شد.",
            "verify_invalid": "کد تأیید نامعتبر است یا منقضی شده. دوباره تلاش کنید یا کد جدید بگیرید.",
            "forgot_prompt": "ایمیل حساب خود را ارسال کنید تا در صورت وجود حساب، کد بازیابی رمز عبور ارسال شود.",
            "forgot_sent": "اگر این حساب وجود داشته باشد، کد بازیابی رمز عبور به ایمیل حساب ارسال شد.\n\nبرای امنیت، رمز جدید خود را در تلگرام ارسال نکنید. از فرم تغییر رمز برنامه/API با همین کد استفاده کنید.",
            "unlink_ask": "آیا مطمئن هستید که می‌خواهید اتصال تلگرام را حذف کنید؟",
            "unlink_choose": "از دکمه‌های پایین <b>بله، قطع اتصال</b> یا <b>لغو</b> را انتخاب کنید.",
            "unlinked": "اتصال حساب تلگرام شما حذف شد.",
            "webapp_missing": "آدرس برنامه وب هنوز تنظیم نشده است.",
            "webapp_open": "برنامه را از اینجا باز کنید: <a href=\"{url}\">باز کردن برنامه</a>",
            "admin_only": "فقط ادمین متصل‌شده می‌تواند از این قابلیت مدیریتی تلگرام استفاده کند.",
            "admin_courses_empty": "هنوز دوره‌ای ساخته نشده است.",
            "course_create_start": "ساخت دوره جدید. ابتدا عنوان دوره را ارسال کنید.",
            "course_short_description_prompt": "توضیح کوتاه دوره را ارسال کنید. حداکثر ۳۰۰ کاراکتر.",
            "course_description_prompt": "توضیح کامل دوره را ارسال کنید، یا برای رد شدن <code>-</code> بفرستید.",
            "course_price_prompt": "قیمت دوره را به عدد ارسال کنید. برای دوره رایگان <code>0</code> بفرستید.",
            "course_duration_prompt": "مدت کل دوره را به دقیقه ارسال کنید. مثال: <code>120</code>",
            "course_level_prompt": "سطح دوره را ارسال کنید: <code>beginner</code>، <code>intermediate</code>، <code>advanced</code> یا <code>all_levels</code>.",
            "course_publish_prompt": "همین الان منتشر شود؟ برای انتشار <code>yes</code> و برای پیش‌نویس <code>no</code> ارسال کنید.",
            "course_created": "✅ دوره با موفقیت ساخته شد.",
            "course_status_updated": "✅ وضعیت دوره به‌روزرسانی شد.",
            "lesson_create_start": "افزودن درس به این دوره. ابتدا عنوان درس را ارسال کنید.",
            "lesson_description_prompt": "توضیح درس را ارسال کنید، یا برای رد شدن <code>-</code> بفرستید.",
            "lesson_content_prompt": "محتوای درس را ارسال کنید، یا برای رد شدن <code>-</code> بفرستید.",
            "lesson_video_url_prompt": "لینک ویدیو را ارسال کنید، یا برای رد شدن <code>-</code> بفرستید.",
            "lesson_duration_prompt": "مدت درس را به دقیقه ارسال کنید. مثال: <code>15</code>",
            "lesson_position_prompt": "شماره ترتیب درس را ارسال کنید، یا برای قرارگیری خودکار در انتها <code>-</code> بفرستید.",
            "lesson_preview_prompt": "آیا این درس پیش‌نمایش رایگان است؟ <code>yes</code> یا <code>no</code> ارسال کنید.",
            "lesson_created": "✅ درس با موفقیت اضافه شد.",
            "course_login_required": "برای خرید دوره، دیدن دوره‌های من یا ثبت دیدگاه ابتدا حساب خود را متصل کنید.",
            "courses_empty": "هنوز دوره منتشرشده‌ای وجود ندارد.",
            "my_courses_empty": "شما هنوز دوره فعالی ندارید.",
            "orders_empty": "شما هنوز سفارشی ندارید.",
            "reviews_empty": "هنوز دیدگاه تأییدشده‌ای وجود ندارد.",
            "review_rating_prompt": "امتیاز این دوره را از ۱ تا ۵ ارسال کنید.",
            "review_title_prompt": "اختیاری: یک عنوان کوتاه برای دیدگاه بفرستید، یا برای رد شدن <code>-</code> ارسال کنید.",
            "review_comment_prompt": "حالا متن دیدگاه خود را ارسال کنید. دیدگاه فقط بعد از تأیید ادمین نمایش داده می‌شود.",
            "review_pending": "✅ ممنون! دیدگاه شما در انتظار تأیید ادمین است.",
            "review_queue_empty": "دیدگاه در انتظار بررسی وجود ندارد.",
            "payment_manual": "✅ سفارش و پرداخت دستی ایجاد شد. ثبت‌نام بعد از تأیید ادمین فعال می‌شود.",
            "payment_success": "✅ پرداخت موفق بود. شما در دوره ثبت‌نام شدید.",
            "payment_created": "✅ سفارش/پرداخت با موفقیت ایجاد شد.",
            "course_already_owned": "شما قبلاً این دوره را خریده‌اید.",
            "create_start": "ساخت کاربر جدید.\n\nابتدا نام کاربری را ارسال کنید.\nمثال: <code>ali_ahmadi</code>",
            "create_email": "حالا آدرس جیمیل کاربر را ارسال کنید.\nمثال: <code>user@gmail.com</code>",
            "create_phone": "حالا شماره موبایل را ارسال کنید.\nمثال: <code>09123456789</code>",
            "create_first_name": "حالا نام کوچک را به فارسی ارسال کنید.\nمثال: <code>علی</code>",
            "create_last_name": "حالا نام خانوادگی را به فارسی ارسال کنید.\nمثال: <code>احمدی</code>",
            "create_choose": "از دکمه‌های پایین <b>ساخت کاربر</b> یا <b>لغو</b> را انتخاب کنید.",
            "create_expired": "زمان ساخت کاربر تمام شد. دوباره نام کاربری را ارسال کنید.",
            "create_duplicate": "کاربری با این نام کاربری، ایمیل یا موبایل وجود دارد. با اطلاعات جدید دوباره شروع کنید.",
            "create_done_followup": "کد تنظیم/بازیابی رمز عبور هم به ایمیل کاربر ارسال شد. کاربر می‌تواند از فرم فراموشی رمز عبور برنامه، رمز خود را تنظیم کند.",
            "create_email_failed": "کاربر ساخته شد، اما ارسال ایمیل تنظیم رمز ناموفق بود. از پنل ادمین یا فرایند فراموشی رمز عبور دوباره ارسال کنید.",
            "link_usage": "روش استفاده: <code>/link your-email@example.com</code>",
            "invalid_username_detail": "نام کاربری نامعتبر است: {error}\n\nدوباره نام کاربری را ارسال کنید.",
            "username_exists": "این نام کاربری وجود دارد. نام کاربری دیگری ارسال کنید.",
            "invalid_create_email_detail": "ایمیل نامعتبر است: {error}\n\nدوباره یک جیمیل معتبر ارسال کنید.",
            "email_exists": "این ایمیل وجود دارد. جیمیل دیگری ارسال کنید.",
            "invalid_phone_detail": "شماره موبایل نامعتبر است: {error}\n\nدوباره شماره موبایل را ارسال کنید.",
            "phone_exists": "این شماره موبایل وجود دارد. شماره دیگری ارسال کنید.",
            "invalid_first_name_detail": "نام کوچک نامعتبر است: {error}\n\nدوباره نام کوچک را ارسال کنید.",
            "invalid_last_name_detail": "نام خانوادگی نامعتبر است: {error}\n\nدوباره نام خانوادگی را ارسال کنید.",
            "create_failed": "ساخت کاربر ناموفق بود: {error}",
            "create_success": "✅ کاربر با موفقیت ساخته شد.\n\nنام کاربری: <code>{username}</code>\nایمیل: <code>{email}</code>\nموبایل: <code>{phone}</code>\n\n{follow_up}",
            "create_confirm_text": "لطفاً اطلاعات کاربر جدید را تأیید کنید:\n\nنام کاربری: <code>{username}</code>\nایمیل: <code>{email}</code>\nموبایل: <code>{phone}</code>\nنام: <code>{first_name}</code>\nنام خانوادگی: <code>{last_name}</code>\n\nهیچ رمزی در تلگرام ارسال نمی‌شود. کاربر رمز خود را با کد ایمیلی تنظیم می‌کند.",
            "yes": "بله",
            "no": "خیر",
            "account_text": "<b>حساب شما</b>\nنام کاربری: <code>{username}</code>\nنام: <code>{first_name}</code>\nنام خانوادگی: <code>{last_name}</code>\nایمیل: <code>{email}</code>\nموبایل: <code>{phone}</code>\nتأیید ایمیل: <code>{verified}</code>",
            "courses_heading": "<b>📚 دوره‌ها</b>",
            "course_list_item": "\n<b>{index}. {title}</b>{rating}\n{description}\nقیمت: <code>{price}</code>",
            "view_course_button": "🔎 {title}",
            "prev_button": "⬅️ قبلی",
            "next_button": "بعدی ➡️",
            "main_menu_button": "⬅️ منوی اصلی",
            "course_detail_text": "<b>{title}</b>\n\n{description}\n\nسطح: <code>{level}</code>\nمدت: <code>{duration} دقیقه</code>\nدرس‌ها: <code>{lessons}</code>\nامتیاز: <code>{rating}</code>\nقیمت: <code>{price}</code>",
            "lessons_button": "🧩 درس‌ها",
            "reviews_button": "⭐ دیدگاه‌ها",
            "buy_button": "🛒 خرید / ثبت‌نام",
            "write_review_button": "✍️ ثبت دیدگاه",
            "courses_back_button": "⬅️ دوره‌ها",
            "course_back_button": "⬅️ دوره",
            "lessons_heading": "<b>🧩 درس‌های {title}</b>",
            "no_lessons": "هنوز درسی برای این دوره منتشر نشده است.",
            "lesson_item": "\n{lock} <b>{position}. {title}</b>\nمدت: <code>{duration} دقیقه</code>",
            "video_line": "ویدیو: {url}",
            "reviews_heading": "<b>⭐ دیدگاه‌های تأییدشده برای {title}</b>",
            "review_item": "\n<b>{rating}/5{title}</b>\nتوسط: <code>{user}</code>\n{comment}",
            "my_courses_heading": "<b>🎓 دوره‌های من</b>",
            "enrollment_item": "\n<b>{title}</b>\nوضعیت: <code>{status}</code>\nتاریخ ثبت‌نام: <code>{enrolled_at}</code>",
            "open_course_button": "باز کردن {title}",
            "my_orders_heading": "<b>🧾 سفارش‌های من</b>",
            "order_item": "\n<b>{order_number}</b>\nدوره‌ها: <code>{courses}</code>\nوضعیت: <code>{status}</code>\nمجموع: <code>{total}</code>",
            "review_saved_with_id": "{message}\nشناسه دیدگاه: <code>{review_id}</code>",
            "review_queue_heading": "<b>🛡 دیدگاه‌های در انتظار بررسی</b>",
            "pending_review_item": "\n<b>{course}</b>\nکاربر: <code>{user}</code> | امتیاز: <code>{rating}/5</code>\n{comment}",
            "approve_button": "✅ تأیید",
            "reject_button": "❌ رد",
            "refresh_button": "به‌روزرسانی",
            "admin_review_note": "بررسی‌شده از ربات تلگرام.",
            "review_moderated": "✅ دیدگاه <code>{review_id}</code> با وضعیت <b>{status}</b> ثبت شد.",
            "back_to_queue_button": "بازگشت به صف بررسی",
            "payment_my_courses_button": "🎓 دوره‌های من",
            "payment_my_orders_button": "🧾 سفارش‌های من",
            "order_payment_order": "سفارش: <code>{order_number}</code>",
            "order_payment_status": "وضعیت: <code>{status}</code>",
            "order_payment_total": "مجموع: <code>{total}</code>",
            "order_payment_payment": "پرداخت: <code>{payment_number}</code>",
            "order_payment_provider": "درگاه: <code>{provider}</code>",
            "order_payment_payment_status": "وضعیت پرداخت: <code>{status}</code>",
            "order_payment_url": "لینک پرداخت: {url}",
            "course_title_invalid": "عنوان دوره باید بین ۳ تا ۱۸۰ کاراکتر باشد.",
            "lesson_title_invalid": "عنوان درس باید بین ۲ تا ۱۸۰ کاراکتر باشد.",
            "lesson_created_detail": "{message}\n\n<b>{title}</b>\nدوره: <code>{course}</code>\nترتیب: <code>{position}</code>",
            "admin_courses_heading": "<b>🧑‍🏫 مدیریت دوره‌ها</b>",
            "admin_course_list_item": "\n<b>{index}. {title}</b>\nوضعیت: <code>{status}</code> | قیمت: <code>{price}</code>",
            "manage_course_button": "مدیریت {title}",
            "admin_course_text": "<b>{title}</b>\n\nوضعیت: <code>{status}</code>\nاسلاگ: <code>{slug}</code>\nسطح: <code>{level}</code>\nمدت: <code>{duration} دقیقه</code>\nدرس‌ها: <code>{lessons}</code>\nقیمت: <code>{price}</code>\n\n{description}",
            "add_lesson_button": "➕ افزودن درس",
            "publish_button": "✅ انتشار",
            "unpublish_button": "📥 پیش‌نویس",
            "archive_button": "🗄 آرشیو",
            "public_view_button": "👁 نمایش عمومی",
            "all_courses_button": "📋 همه دوره‌ها",
            "help_text": "<b>گزینه‌های موجود</b>\nاز دکمه‌های پایین استفاده کنید و نیازی به تایپ دستور نیست.\n\n🔗 <b>اتصال حساب</b> - اتصال حساب برنامه به تلگرام\n👤 <b>حساب من</b> - نمایش اطلاعات حساب متصل‌شده\n✅ <b>تأیید ایمیل</b> - ارسال و بررسی کد تأیید ایمیل\n🔐 <b>فراموشی رمز عبور</b> - ارسال کد بازیابی رمز عبور\n➕ <b>ساخت کاربر</b> - فقط برای ادمین\n🌐 <b>باز کردن برنامه</b> - باز کردن برنامه وب\n🌍 <b>زبان</b> - تغییر زبان ربات\n🚪 <b>قطع اتصال</b> - حذف اتصال تلگرام",
            "placeholder_language": "Language / زبان",
            "placeholder_main_menu": "یک گزینه را انتخاب کنید",
            "placeholder_cancel": "مقدار خواسته‌شده را ارسال کنید یا لغو کنید",
            "placeholder_confirm": "تأیید یا لغو",
        },
    }


class TelegramCommerceMessagesVO:
    AUTH_REQUIRED = "Please link your account before using this feature."
    COURSE_NOT_FOUND = "Course not found or not published."
    EMPTY_COURSES = "No published courses are available yet."
    EMPTY_REVIEWS = "No approved reviews yet."
    EMPTY_ENROLLMENTS = "You do not have any active courses yet."
    EMPTY_ORDERS = "You do not have any orders yet."
    REVIEW_PENDING = "Thanks! Your review was saved and is waiting for admin approval."
    PAYMENT_CREATED = "Payment/order was created."
    PAYMENT_SUCCEEDED = "Payment succeeded. You are now enrolled."
    MANUAL_PAYMENT_CREATED = "Manual payment was created. Admin confirmation is required before enrollment."
    ALREADY_PURCHASED = "You already purchased this course."
    ADMIN_EMPTY_REVIEWS = "There are no pending reviews."


class TelegramBotProfileVO:
    DESCRIPTION = {
        TelegramBotLanguageVO.FA: (
            "سلام! به ربات Devixa خوش آمدید. 👋\n\n"
            "با این ربات می‌توانید دوره‌ها را ببینید، خرید و ثبت‌نام انجام دهید، "
            "سفارش‌ها و دوره‌های خود را پیگیری کنید، دیدگاه ثبت کنید، حساب را متصل کنید "
            "و اگر مدیر باشید کاربران و دیدگاه‌ها را مدیریت کنید.\n\n"
            "برای شروع، دکمه Start را بزنید."
        ),
        TelegramBotLanguageVO.EN: (
            "Welcome to Devixa bot. 👋\n\n"
            "Use this bot to browse and buy courses, track orders and enrollments, "
            "submit reviews, link your account, verify email, recover password, "
            "and manage users/reviews if you are an admin.\n\n"
            "Tap Start to begin."
        ),
    }
    SHORT_DESCRIPTION = {
        TelegramBotLanguageVO.FA: "دوره‌ها، خرید، سفارش‌ها، دیدگاه‌ها و مدیریت حساب Devixa",
        TelegramBotLanguageVO.EN: "Browse courses, buy, review, track orders, and manage your Devixa account.",
    }
    COMMANDS = {
        TelegramBotLanguageVO.FA: [
            {"command": "start", "description": "شروع و نمایش منو"},
            {"command": "courses", "description": "مشاهده دوره‌ها"},
            {"command": "my_courses", "description": "دوره‌های من"},
            {"command": "orders", "description": "سفارش‌های من"},
            {"command": "channels", "description": "کانال‌های رسمی"},
            {"command": "admin_courses", "description": "مدیریت دوره‌ها - فقط ادمین"},
            {"command": "create_course", "description": "ساخت دوره - فقط ادمین"},
            {"command": "review_queue", "description": "بررسی دیدگاه‌ها - فقط ادمین"},
            {"command": "account", "description": "نمایش حساب من"},
            {"command": "verify_email", "description": "تأیید ایمیل"},
            {"command": "forgot_password", "description": "بازیابی رمز عبور"},
            {"command": "language", "description": "تغییر زبان"},
            {"command": "help", "description": "راهنما"},
        ],
        TelegramBotLanguageVO.EN: [
            {"command": "start", "description": "Start and show menu"},
            {"command": "courses", "description": "Browse courses"},
            {"command": "my_courses", "description": "My courses"},
            {"command": "orders", "description": "My orders"},
            {"command": "channels", "description": "Official channels"},
            {"command": "admin_courses", "description": "Manage courses - admin only"},
            {"command": "create_course", "description": "Create course - admin only"},
            {"command": "review_queue", "description": "Review queue - admin only"},
            {"command": "account", "description": "Show my account"},
            {"command": "verify_email", "description": "Verify email"},
            {"command": "forgot_password", "description": "Recover password"},
            {"command": "language", "description": "Change language"},
            {"command": "help", "description": "Help"},
        ],
    }
    SETUP_SUCCESS_MESSAGE = "Telegram bot profile UX was updated successfully."
