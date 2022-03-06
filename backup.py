import os
import email
import base64
import mailbox
import logging
import asyncio
import requests
import argparse
from urllib.parse import urlencode
from oauth_utils import oauth_authorize

TOKEN = {}
loop = asyncio.get_event_loop()


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
    parser.add_argument('--search-query', required=True,
                        dest='search_query', help='Query to search messages')
    parser.add_argument('--output-dir', required=True,
                        dest='output_maildir', help='Output Maildir')
    parser.add_argument('--debug', action='store_true', required=False,
                        default=False, dest='debug', help='Print debug info')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    scope = "https://www.googleapis.com/auth/gmail.readonly"
    oauth_authorize(
        loop,
        TOKEN,
        scope,
        args.client_id,
        args.client_secret,
        args.redirect_uri
    )
    params = {
        "q": args.search_query,
        "maxResults": 100,
    }

    # Store in a output Maildir folder
    if not os.path.exists(args.output_maildir):
        os.makedirs(args.output_maildir)
    maildir = mailbox.Maildir(args.output_maildir, create=True)
    session = requests.Session()

    def _main():
        payload = search_messages(session, params)
        messages = [ii['id'] for ii in payload.get('messages', [])]
        for msg_id in messages:
            raw_message = get_message(session, msg_id)

            # Build a MaildirMessage
            message = email.message_from_bytes(raw_message)
            msg = mailbox.MaildirMessage(message)
            msg.set_flags("S")
            maildir.add(msg)

        if payload.get("nextPageToken"):
            params["pageToken"] = payload["nextPageToken"]
            loop.call_soon(_main)
        else:
            loop.stop()
    loop.call_soon(_main)
    loop.run_forever()


def search_messages(session, params):
    response = session.get(
        "https://www.googleapis.com/gmail/v1/"
        "users/me/messages?{0}".format(urlencode(params)),
        headers={
            "Authorization": "Bearer {0}".format(TOKEN['access_token']),
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "Gmail Backup (gzip)",
        }
    )
    if not response.ok:
        raise ResponseException(response.json())
    json_resp = response.json()
    logging.debug(
        "Approximately {0} messages for {1} page token".format(
            json_resp["resultSizeEstimate"], params.get("pageToken", "")
        )
    )
    return json_resp


def get_message(session, msg_id):
    response = session.get(
        "https://www.googleapis.com/gmail/v1/users/me/messages/{0}?format=raw".format(msg_id),
        headers={
            "Authorization": "Bearer {0}".format(TOKEN['access_token']),
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "Gmail Backup (gzip)",
        }
    )
    if not response.ok:
        raise ResponseException(response.json())
    json_resp = response.json()
    return base64.urlsafe_b64decode(json_resp["raw"])


def store_messages(maildir, msgs):
    if len(msgs) == 0:
        return None

    loop.call_soon(store_messages, *(maildir, msgs[1:]))


if __name__ == '__main__':
    main()
