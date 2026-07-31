from . import context


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class AuditContextMiddleware:
    """요청마다 actor/ip를 audit.context에 심는다. AuthenticationMiddleware 다음에 둔다."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            actor_id = str(user.pk)
            actor_type = "admin" if user.is_staff else "user"
        else:
            actor_id = None
            actor_type = "system"
        context.set_context(actor_id, actor_type, _client_ip(request))
        return self.get_response(request)
