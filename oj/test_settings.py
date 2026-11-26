"""Isolated functional tests; never connects to the running OJ database or judge queue."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = "isolated-oj-functional-tests"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
INSTALLED_APPS = [
    "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions",
    "django.contrib.staticfiles", "rest_framework", "django_dramatiq",
    "account", "announcement", "conf", "problem", "contest", "utils", "submission", "options", "judge",
]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
AUTH_USER_MODEL = "account.User"
ROOT_URLCONF = "oj.urls"
USE_TZ = True
TIME_ZONE = "UTC"
MIDDLEWARE = ["django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
              "django.contrib.auth.middleware.AuthenticationMiddleware", "account.middleware.SessionRecordMiddleware"]
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True}]
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
DRAMATIQ_BROKER = {"BROKER": "dramatiq.brokers.stub.StubBroker", "OPTIONS": {}, "MIDDLEWARE": [
    "dramatiq.middleware.AgeLimit", "dramatiq.middleware.TimeLimit", "dramatiq.middleware.Callbacks", "dramatiq.middleware.Retries"]}
AVATAR_URI_PREFIX = "/public/avatar"
AVATAR_UPLOAD_DIR = os.path.join(BASE_DIR, "data", "public", "avatar")
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "public", "upload")
UPLOAD_PREFIX = "/public/upload"
TEST_CASE_DIR = os.path.join(BASE_DIR, "data", "test_case")
DATA_DIR = os.path.join(BASE_DIR, "data")
IP_HEADER = "HTTP_X_REAL_IP"
STATIC_URL = "/public/"
REST_FRAMEWORK = {"TEST_REQUEST_DEFAULT_FORMAT": "json"}
