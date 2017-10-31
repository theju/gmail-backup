import time
import email
import base64
import random
import mailbox
import logging
import requests
import argparse
from urllib.parse import urlencode


def main():
    parser = argparse.ArgumentParser(
        description='Backup gmail mails matching a search query into a Maildir'
    )
    parser.add_argument('--client-id', required=False,
                        dest='client_id', help='Google Client id')
    parser.add_argument('--client-secret', required=False,
                        dest='client_secret', help='Google Client secret')
    parser.add_argument('--redirect-uri', required=False,
                        dest='redirect_uri', help='OAuth redirect uri')
    parser.add_argument('--access-token', required=False,
                        dest='access_token', help='Existing access token (if any)')
    parser.add_argument('--search-query', required=True,
                        dest='search_query', help='Query to search messages')
    parser.add_argument('--output-dir', required=True,
                        dest='output_maildir', help='Output Maildir')
    parser.add_argument('--debug', action='store_true', required=False,
                        default=False, dest='debug', help='Print debug info')

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if args.access_token:
        access_token = args.access_token
    else:
        access_token = oauth_authorize(
            args.client_id,
            args.client_secret,
            args.redirect_uri
        )
    params = {
        "access_token": access_token,
        "q": args.search_query
    }
    messages_list = []
    while True:
        time.sleep(0.5)
        payload = search_messages(params)
        for message in payload["messages"]:
            messages_list.append(message["id"])
        if payload.get("nextPageToken"):
            params["pageToken"] = payload["nextPageToken"]
        else:
            break

    # Store in a output Maildir folder
    maildir = mailbox.Maildir(args.output_maildir)

    num_pages = int(len(messages_list) / 10 + 1)
    for ii in range(num_pages):
        logging.debug("Fetching page {0} of {1}".format(ii + 1, num_pages))
        time.sleep(0.5)
        messages = get_messages(
            access_token,
            messages_list[ii * 10 : ii * 10 + 10]
        )
        # Build a MaildirMessage
        for raw_message in messages:
            message = email.message_from_bytes(raw_message)
            msg = mailbox.MaildirMessage(message)
            msg.set_flags("S")
            maildir.add(msg)


def search_messages(params):
    response = requests.get(
        "https://www.googleapis.com/gmail/v1/"
        "users/me/messages?{0}".format(urlencode(params)),
        headers={
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "Gmail Backup (gzip)"
        }
    )
    if not response.ok:
        raise Exception(response.content)
    json_resp = response.json()
    logging.debug(
        "Approximately {0} messages for {1} page token".format(
            json_resp["resultSizeEstimate"], params.get("pageToken", "")
        )
    )
    return json_resp


def get_messages(access_token, msgs_id):
    # TODO: Replace with batch request
    for msg_id in msgs_id:
        response = requests.get(
            "https://www.googleapis.com/gmail/v1/users/me/messages/{0}?format=raw".format(msg_id),
            headers={"Authorization": "Bearer {0}".format(access_token)}
        )
        if not response.ok:
            continue
        json_resp = response.json()
        yield base64.urlsafe_b64decode(json_resp["raw"])


def oauth_authorize(client_id, client_secret, redirect_uri):
    state = int(random.random() * 1000)
    params = urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/gmail.readonly",
        "state": state
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
    if not response.ok:
        raise Exception(response.content)
    logging.debug(response.json())
    token = response.json()['access_token']
    return token


if __name__ == '__main__':
    main()
