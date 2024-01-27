import requests
from settings.settings import ENCODED_CREDENTIALS

# before you continiue....

# import base64
# def encode_credentials() -> str:
#     """
#     Encode APP_ID and CERT_ID to Base64.

#     Parameters:
#     app_id (str): Your eBay Application ID (Client ID).
#     cert_id (str): Your eBay Certificate ID (Client Secret).

#     Returns:
#     str: Base64-encoded credentials string.
#     """
#     app_id = os.getenv('APP_ID')
#     cert_id = os.getenv('CERT_ID')
#     credentials = f"{app_id}:{cert_id}"

#     credentials_bytes = credentials.encode('utf-8')  # Convert string to bytes
#     base64_credentials = base64.b64encode(credentials_bytes)  # Encode bytes to base64
#     return base64_credentials.decode('utf-8')  # Convert bytes back to string


def get_app_token():
    url = "https://api.ebay.com/identity/v1/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {ENCODED_CREDENTIALS}",
    }

    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope",
    }

    response = requests.post(url, headers=headers, data=data)
    token_info = response.json()
    return token_info
    # access_token = token_info.get('access_token')
    # return access_token
