import requests
import logging
from datetime import datetime
from datetime import timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RemoteSDAPList:
    list: dict
    outdated_at: datetime


class CollectionNotFound(Exception):
    pass


class RemoteSDAPCache:
    def __init__(self):
        self.sdap_lists = {}

    def _add(self, url, timeout=2, max_age=3600*24):
        list_url = f"{url}/list"
        try:
            r = requests.get(list_url, timeout=timeout)
            if r.status_code == 200:
                logger.info("Caching list for sdap %s: %s", list_url, r.text)
                self.sdap_lists[url] = RemoteSDAPList(
                    list=r.json(),
                    outdated_at=datetime.now()+timedelta(seconds=max_age)
                )
            else:
                raise CollectionNotFound(f"url {list_url} was not reachable, responded with status {r.status_code}")
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as e:
            raise CollectionNotFound(f"url {list_url} was not reachable in {timeout} s")

    def get(self, url, short_name):
        stripped_url = url.strip('/')
        if stripped_url not in self.sdap_lists or self.sdap_lists[stripped_url].outdated_at>datetime.now():
            self._add(stripped_url)

        for collection in self.sdap_lists[stripped_url].list:
            if 'shortName' in collection and collection['shortName'] == short_name:
                return collection

        raise CollectionNotFound(f"collection {short_name} has not been found in url {stripped_url}")