from typing import Union, Optional
from datetime import timedelta
from redis import StrictRedis


class Cache:
    def __init__(self: 'Cache', config: dict):
        self._config = config
        self._redis = StrictRedis()

    def write(self: 'Cache', key: str, value: str, expiry: Optional[Union[timedelta, int]] = None):
        # Yes, we have a default cache duration and then a default default cache duration. Shush.
        if expiry is None:
            expiry = self._config.get('default_cache_duration', 600)

        if isinstance(expiry, timedelta):
            expiry = expiry.total_seconds()

        expiry = min(expiry, self._config.get('max_cache_duration', 86400))
        self._redis.setex(key, expiry, value)

    def read(self: 'Cache', key: str, raise_if_absent: bool = False):
        val = self._redis.get(key)
        if val is None and raise_if_absent is True:
            raise KeyError(key)

        return val

    def delete(self, keys: Union[str, list], raise_if_absent: bool = False):
        if raise_if_absent:
            if isinstance(keys, str):
                keys = [keys]

            keys_exist = [self._redis.exists(x) for x in keys]
            if list(set(keys_exist)) != [True]:
                raise KeyError(keys[keys_exist.index(False)])

        self._redis.delete(keys)
