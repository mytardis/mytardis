from django.conf import settings

from social_core.backends.oauth import BaseOAuth2


class AAFOpenId(BaseOAuth2):
    """AAF OpenID Authentication backend"""

    name = "aaf"
    DEFAULT_SCOPE = ["openid", "email", "profile"]
    AUTHORIZATION_URL = getattr(settings, "SOCIAL_AUTH_AAF_AUTH_URL", None)
    ACCESS_TOKEN_URL = getattr(settings, "SOCIAL_AUTH_AAF_TOKEN_URL", None)
    USER_INFO_URL = getattr(settings, "SOCIAL_AUTH_AAF_USER_INFO_URL", None)
    REDIRECT_STATE = False
    ACCESS_TOKEN_METHOD = "POST"
    ID_KEY = "email"

    def get_user_details(self, response):
        """returns user details from AAF"""
        return {
            "username": response.get("email"),
            "email": response.get("email") or "",
            "first_name": response.get("given_name") or "",
            "last_name": response.get("family_name") or "",
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        """
        import requests
        import json
        try:
            headers = {'Authorization': 'Bearer ' + access_token}
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            response = requests.get(self.USER_INFO_URL, headers=headers)
            d = json.loads(response.content.decode())
            return d
        except ValueError:
            return None
       """
        return self.get_json(
            self.USER_INFO_URL,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": "Bearer " + access_token,
            },
        )

    def auth_headers(self):
        return {"Content-Type": "application/x-www-form-urlencoded"}
