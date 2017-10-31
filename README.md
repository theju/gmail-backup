# Gmail Backup

A [NIH](https://en.wikipedia.org/wiki/Not_invented_here) script to export gmail
e-mails matching a search query into a [Maildir](https://en.wikipedia.org/wiki/Maildir).

It is powered by the [Gmail API](https://developers.google.com/gmail/api/guides/).

## Prerequisites

You need to create an application at the (Google Developer console)[https://console.developers.google.com/]
before using the project. Create a new project and enable the Gmail API and create an OAuth
client and obtain the client-id and client-secret.

Install the requirements for the project located in the `requirements.txt`

## Usage

```

$ python script.py --client-id <client_id> --client-secret <client_secret> \
                   --search-query "before:2015/01/01 after:2014/01/01" \
                   --output-dir ~/gmail/2015
```

## License

MIT License. Refer the `LICENSE` file.
