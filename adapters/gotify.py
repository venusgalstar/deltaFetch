import argparse
import logging
import os

import requests

from model import WatchResult
from . import SendAdapter


class GotifySendAdapter(SendAdapter):
    def __init__(self, args):
        self.args = self._parse_args(args)

    def send(self, data: WatchResult) -> bool:
        url = f'{self.args.gotify_url}/message'
        r = requests.post(
            url,
            json={
                'title': 'Website has changed!',
                'message': f'Difference is {data.diff} characters.\nCheck {data.url}',
                'priority': 2
            },
            headers={
                'X-Gotify-Key': self.args.gotify_key
            }
        )
        if r.status_code != 200:
            logging.error(r.text)
            return False
        return True

    @classmethod
    def get_parser(cls) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog=f'Website Watcher – "{cls.get_name()}" Adapter',
                                         description=cls.get_description())
        parser.add_argument('--gotify_key', required=True, type=str, help='Gotify app key / token')
        parser.add_argument('--gotify_url', required=True, type=cls._valid_url, help='Gotify server instance address')
        return parser

    @classmethod
    def get_name(cls) -> str:
        return os.path.basename(__file__)[:-3]

    @classmethod
    def get_description(cls) -> str:
        return 'An adapter to send push messages via Gotify (https://gotify.net).'


adapter = GotifySendAdapter
