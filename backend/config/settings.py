"""
올라케어 백엔드 설정.

로컬 개발은 SQLite(설치 불필요), CI·배포는 PostgreSQL — DATABASE_URL 환경변수로 전환한다.
근거: docs/08_tech_stack.md §1, §6 / docs/06_decisions.md #16
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-dev-only-change-in-prod")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    # docs/08_tech_stack.md §2 저장소 구조
    "apps.accounts",
    "apps.audit",
    "apps.consent",
    "apps.privacy",
    "apps.content",
    "apps.clinic",
    "apps.diagnosis",
    "apps.support",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # 감사로그의 actor/ip를 요청 컨텍스트에 심는다. docs/02_architecture_constraints.md §1
    "apps.audit.middleware.AuditContextMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        # docs/08_tech_stack.md: Django Template을 쓰지 않는다 — 백엔드는 JSON API만 낸다.
        # APP_DIRS는 admin 자체 템플릿(로그인 화면 등)에 필요해 켜둔다.
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# 로컬은 SQLite 기본값, DATABASE_URL이 있으면(CI·배포) 그걸 쓴다.
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── 업로드 이미지. docs/04_design_system.md §4 — 파일 스토리지에 저장하고 경로만
# DB에 남긴다(base64 인라인 금지). 정식 배포 전환(§10-1) 시 오브젝트 스토리지로
# 바꾸되, 지금은 로컬 디스크로 충분하다(§10-0).
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ── DRF: 기본 거부. docs/08_tech_stack.md §5 ─────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# ── CSRF. Vite dev proxy(changeOrigin: true)는 Host 헤더를 127.0.0.1:8000으로
# 바꿔 보내지만 브라우저의 Origin 헤더는 그대로 프론트 오리진(5173/5174)이라
# Django의 Origin↔Host 비교가 실패한다. 로컬 개발 프론트 두 개만 신뢰 오리진으로 연다.
# docs/08_tech_stack.md §6 "Vite dev proxy" 참고.
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS", default=["http://localhost:5173", "http://localhost:5174"]
)

# ── 세션 쿠키. docs/08_tech_stack.md §3 ──────────────────────────
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=not DEBUG)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=not DEBUG)

# ── 배포 보안 기본값. docs/08_tech_stack.md §9 "manage.py check --deploy 통과" ──
# ★ SECURE_SSL_REDIRECT를 DEBUG=False일 때 자동으로 켰더니 CI의 테스트 클라이언트가
# 전부 301로 튕겨나가 실패했다(2026-07-31). 우리 배포 구조(§10-1)는 nginx가 TLS를
# 종료하고 Django엔 평문 HTTP로 넘기므로, 여기서 무작정 True로 켜면 오히려
# SECURE_PROXY_SSL_HEADER 없이는 리다이렉트 루프가 날 수 있다. 그래서 기본은 False로
# 두고, 실제 배포에서 nginx가 X-Forwarded-Proto를 보내도록 설정한 뒤
# SECURE_PROXY_SSL_HEADER와 함께 환경변수로만 켠다. check --deploy는 이 상태에서
# W008 경고만 내고 통과한다(경고는 실패 아님).
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)

# ── 판별 어댑터 기본값. docs/02_architecture_constraints.md §3 ──
DIAGNOSIS_PROVIDER = env("DIAGNOSIS_PROVIDER", default="mock")
