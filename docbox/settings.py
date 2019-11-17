import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG", False)

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(";")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.forms",
    "social_django",
    "docbox.apps.DocboxConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "docbox.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "docbox.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE"),
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "HOST": os.getenv("DB_HOST"),
        "ATOMIC_REQUESTS": True,
    }
}

AUTHENTICATION_BACKENDS = (
    "social_core.backends.google.GoogleOAuth2",
    "social_core.backends.github.GithubOAuth2",
)

LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Kiev"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/static/"

LOGIN_URL = os.getenv("LOGIN_URL")
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

SOCIAL_AUTH_POSTGRES_JSONFIELD = True

SOCIAL_AUTH_GOOGLE_OPENIDCONNECT_KEY = os.getenv("SOCIAL_AUTH_GOOGLE_OPENIDCONNECT_KEY")
SOCIAL_AUTH_GOOGLE_OPENIDCONNECT_SECRET = os.getenv("SOCIAL_AUTH_GOOGLE_OPENIDCONNECT_SECRET")
SOCIAL_AUTH_GOOGLE_OPENIDCONNECT_WHITELISTED_EMAILS = os.getenv(
    "SOCIAL_AUTH_GOOGLE_OPENIDCONNECT_WHITELISTED_EMAILS"
).split(";")

SOCIAL_AUTH_GITHUB_KEY = os.getenv("SOCIAL_AUTH_GITHUB_KEY")
SOCIAL_AUTH_GITHUB_SECRET = os.getenv("SOCIAL_AUTH_GITHUB_SECRET")
SOCIAL_AUTH_GITHUB_SCOPE = ["user:email"]
SOCIAL_AUTH_GITHUB_WHITELISTED_EMAILS = os.getenv(
    "SOCIAL_AUTH_GITHUB_WHITELISTED_EMAILS"
).split(";")
