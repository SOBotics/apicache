from typing import Union, Optional, Any
from datetime import timedelta, datetime
from dateutil.parser import parse
import itertools
import json
from redis import StrictRedis
import requests


class Cache:
    def __init__(self: 'Cache', config: dict) -> None:
        self._config = config
        self._redis = StrictRedis(host=config.get('redis_host', None), port=config.get('redis_port', None))

    def _write(self: 'Cache', key: str, value: str, expiry: Optional[Union[timedelta, int]] = None) -> None:
        # Yes, we have a default cache duration and then a default default cache duration. Shush.
        if expiry is None:
            expiry = self._config.get('default_cache_duration', 600)

        if isinstance(expiry, timedelta):
            expiry = expiry.total_seconds()

        expiry = min(expiry, self._config.get('max_cache_duration', 86400))
        self._redis.setex(key, expiry, value)
        self._redis.setex(key + ':time', expiry, datetime.utcnow())

    def _read(self: 'Cache', key: str, raise_if_absent: bool = False) -> tuple:
        val = self._redis.get(key)
        insert_time = self._redis.get(key + ':time')
        parsed_time = parse(insert_time) if insert_time is not None else None
        if val is None and raise_if_absent is True:
            raise KeyError(key)

        return val, parsed_time

    def _delete(self: 'Cache', keys: Union[str, list], raise_if_absent: bool = False) -> None:
        if raise_if_absent:
            if isinstance(keys, str):
                keys = [keys]

            keys_exist = [self._redis.exists(x) for x in keys]
            if list(set(keys_exist)) != [True]:
                raise KeyError(keys[keys_exist.index(False)])

        self._redis.delete(keys)

    def _valid(self: 'Cache', key: str, max_age: Optional[Union[int, timedelta]] = None) -> bool:
        exists = self._redis.exists(key)
        if exists:
            if max_age is not None:
                timestamp_exists = self._redis.exists(key + ':time')
                if not timestamp_exists:
                    return False

                inserted_at = parse(self._redis.get(key + ':time'))
                if type(max_age) == int:
                    max_age = timedelta(seconds=max_age)

                return inserted_at > datetime.utcnow() - max_age
            else:
                return True
        else:
            return False

    def get_post_set(self: 'Cache', ids: list, key: str, site: str,
                     expiry: Optional[Union[int, timedelta]] = None,
                     max_age: Optional[Union[int, timedelta]] = None) -> set:
        existing = [x for x in ids if self._valid(str(x), max_age)]
        existing_posts = [self._read(str(x))[0] for x in existing]
        required = [x for x in ids if x not in existing]

        group_size = 100
        request_groups = [list(group) for key, group in
                          itertools.groupby(required, lambda x: required.index(x) // group_size)]
        filter = '!)rCcH8tl2x*c7j30PSR('

        for group in request_groups:
            url = 'https://api.stackexchange.com/2.2/posts/{}?key={}&filter={}&pagesize=100&site={}'\
                  .format(';'.join(group), key, filter, site)
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()['items']
            for post in data:
                self._write(str(post['post_id']), json.dumps(post), expiry=expiry)

        required_posts = [self._read(str(x))[0] for x in required]
        print("Of {}: {} returned from cache and {} requested from SE API"
              .format(len(ids), len(existing), len(required)))
        return set([x for x in existing_posts + required_posts if x is not None])

    def get_recent_questions(self: 'Cache', key: str, site: str,
                             expiry: Optional[Union[int, timedelta]] = None,
                             max_age: Optional[Union[int, timedelta]] = None) -> list:
        if self._valid('recent_questions', max_age):
            print('Valid recent questions list exists, reading from cache with supplement')
            ids = self._read('recent_questions')[0].decode('utf-8').split(';')
            return [json.loads(x.decode('utf-8')) for x in self.get_post_set(ids, key, site, expiry, max_age)]
        else:
            print('No valid recent questions list, sourcing from API')
            filter = '!-MQ9xUObaj3LoqHtm(M_BlElks5TrJ)dF'
            url = 'https://api.stackexchange.com/2.2/questions?key={}&filter={}&pagesize=100&site={}'\
                  .format(key, filter, site)
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()['items']
            qids = []
            for question in data:
                qid = str(question['question_id'])
                self._write(qid, json.dumps(question), expiry=expiry)
                qids.append(qid)

            self._write('recent_questions', ';'.join(qids))
            return data

