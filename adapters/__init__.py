import argparse
import importlib
import logging
from abc import ABC, abstractmethod
from typing import List, Any, Tuple

from model import WatchResult
from utils.url import parse_url

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)


class SendAdapterFactory:
    @classmethod
    def get(cls, name: str, args: List[str]) -> 'SendAdapter':
        return cls.get_class(name).adapter(args)

    @classmethod
    def get_class(cls, name: str):
        try:
            return importlib.import_module(f'.{name}', package='adapters')
        except ModuleNotFoundError:
            logging.error(f'No adapter found with name {name}')
            return None


class SendAdapter(ABC):
    def _parse_args(self, args: List[str]):
        parser = self.get_parser()

        try:
            return parser.parse_args(args)
        except SystemExit as e:
            logging.info(f'For addition help try running "python watcher.py help {self.get_name()}"')
            raise e

    @abstractmethod
    def send(self, data: WatchResult) -> bool:
        pass

    @classmethod
    @abstractmethod
    def get_parser(cls) -> argparse.ArgumentParser:
        pass

    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def get_description(cls) -> str:
        pass

    @staticmethod
    def _valid_url(string: str) -> str:
        url = parse_url(string)
        if url is None:
            raise argparse.ArgumentTypeError('not a valid url')
        return url
