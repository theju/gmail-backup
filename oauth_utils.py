import random
import logging
import requests
from urllib.parse import urlencode


class ResponseException(Exception):
    pass


def oauth_authorize(loop, TOKEN, scope, client_id, client_secret, redirect_uri):
    state = int(random.random() * 1000)
    params = urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "state": state,
        "access_type": "offline",
        "prompt": "consent"
    })
    url = "https://accounts.google.com/o/oauth2/v2/auth?{0}".format(params)
    print("URL is : {0}".format(url))
    auth_code = input("Enter the authorization code: ")
    auth_params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "code": auth_code
    }
    response = requests.post(
        "https://www.googleapis.com/oauth2/v4/token", data=auth_params
    )
    json_resp = response.json()
    if not response.ok:
        raise ResponseException(json_resp)
    logging.debug(json_resp)
    for (key, val) in json_resp.items():
        TOKEN[key] = val

    refresh_token = json_resp['refresh_token']
    args = (loop, TOKEN, client_id, client_secret, refresh_token)
    loop.call_later((json_resp['expires_in'] - 300), oauth_renew, *args)


def oauth_renew(loop, TOKEN, client_id, client_secret, refresh_token):
    auth_params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    response = requests.post(
        "https://www.googleapis.com/oauth2/v4/token", data=auth_params
    )
    json_resp = response.json()
    if not response.ok:
        raise ResponseException(json_resp)
    logging.debug(json_resp)
    for (key, val) in json_resp.items():
        TOKEN[key] = val
    args = (loop, TOKEN, client_id, client_secret, refresh_token)
    loop.call_later((json_resp['expires_in'] - 300), oauth_renew, *args)
