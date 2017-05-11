from typing import Union, Optional
from datetime import timedelta
import itertools
import json
from redis import StrictRedis
import requests


class Cache:
    def __init__(self: 'Cache', config: dict):
        self._config = config
        self._redis = StrictRedis(host=config.get('redis_host', None), port=config.get('redis_port', None))

    def _write(self: 'Cache', key: str, value: str, expiry: Optional[Union[timedelta, int]] = None):
        # Yes, we have a default cache duration and then a default default cache duration. Shush.
        if expiry is None:
            expiry = self._config.get('default_cache_duration', 600)

        if isinstance(expiry, timedelta):
            expiry = expiry.total_seconds()

        expiry = min(expiry, self._config.get('max_cache_duration', 86400))
        self._redis.setex(key, expiry, value)

    def _read(self: 'Cache', key: str, raise_if_absent: bool = False):
        val = self._redis.get(key)
        if val is None and raise_if_absent is True:
            raise KeyError(key)

        return val

    def _delete(self: 'Cache', keys: Union[str, list], raise_if_absent: bool = False):
        if raise_if_absent:
            if isinstance(keys, str):
                keys = [keys]

            keys_exist = [self._redis.exists(x) for x in keys]
            if list(set(keys_exist)) != [True]:
                raise KeyError(keys[keys_exist.index(False)])

        self._redis.delete(keys)

    def get_post_set(self: 'Cache', ids: list, key: str, site: str):
        existing = [x for x in ids if self._redis.exists(str(x))]
        required = ids - existing

        group_size = 100
        request_groups = [list(group) for key, group in itertools.groupby(required, lambda x: x // group_size)]
        filter = '!b0OfN.wXSdUuN('

        for group in request_groups:
            url = 'https://api.stackexchange.com/2.2/posts/{}?key={}&filter={}&pagesize=100&site={}'\
                  .format(';'.join(group), key, filter, site)
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()['items']
            for post in data:
                self._write(str(post['post_id']), json.dumps(post))

        return [self._redis.get(str(x)) for x in ids]
