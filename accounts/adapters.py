from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if not getattr(user, "username", None):
            user.username = self._unique_username(data.get("email") or "")
        return user

    @staticmethod
    def _unique_username(email: str) -> str:
        User = get_user_model()
        base = (email.split("@")[0] if email else "user").lower() or "user"
        candidate = base[:140]
        while User.objects.filter(username=candidate).exists():
            candidate = f"{base[:140]}-{get_random_string(6)}"
        return candidate
