from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


def unique_username(email: str) -> str:
    User = get_user_model()
    base = (email.split("@")[0] if email else "user").lower() or "user"
    candidate = base[:140]
    while User.objects.filter(username=candidate).exists():
        candidate = f"{base[:140]}-{get_random_string(6)}"
    return candidate


class AccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        if not getattr(user, "username", None):
            user.username = unique_username(user.email or "")
        if commit:
            user.save()
        return user


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if not getattr(user, "username", None):
            user.username = unique_username(data.get("email") or "")
        return user
