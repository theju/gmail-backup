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
        description='Delete gmail mails matching a search query'
    )
    parser.add_argument('--client-id', required=False,
                        dest='client_id', help='Google Client id')
    parser.add_argument('--client-secret', required=False,
                        dest='client_secret', help='Google Client secret')
    parser.add_argument('--redirect-uri', required=False,
                        dest='redirect_uri', help='OAuth redirect uri')
    parser.add_argument('--search-query', required=True,
                        dest='search_query', help='Query to search messages')
    parser.add_argument('--debug', action='store_true', required=False,
                        default=False, dest='debug', help='Print debug info')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    scope = "https://mail.google.com/"
    oauth_authorize(
        loop,
        TOKEN,
        scope,
        args.client_id,
        args.client_secret,
        args.redirect_uri
    )
    session = requests.Session()
    params = {
        "q": args.search_query,
        "maxResults": 100,
    }
    def _main():
        payload = search_messages(session, params)
        message_ids = [ii['id'] for ii in payload.get('messages', [])]
        print(message_ids)
        if len(message_ids) > 0:
            resp = requests.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/batchDelete",
                json={"ids": message_ids},
                headers={
                    "Authorization": "Bearer {0}".format(TOKEN['access_token']),
                    "Accept-Encoding": "gzip, deflate",
                    "User-Agent": "Gmail Backup (gzip)",
                }
            )
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


if __name__ == '__main__':
    main()
