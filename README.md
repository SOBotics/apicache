# apicache
Caches SE API responses to save on API quota

## What?
APICache is just that - an API cache. Instead of making requests to the Stack Exchange API, bots make API requests to 
APICache instead. APICache proxies the Stack Exchange API and caches its responses for a set period of time. This way,
if two bots want the same data at similar times, only one request to the SE API is fired and only one quota decreases,
instead of both taking a hit.

## Usage
Parameters operate identically to their equivalents in the Stack Exchange API unless otherwise noted. Additionally,
response format will be the same as the Stack Exchange API where possible, unless otherwise noted. 

Currently supported routes:

 - `/questions/<ids>`: alias of `/posts/<ids>`
 - `/answers/<ids>`: alias of `/posts/<ids>`
 - `/posts/<ids>`: returns posts specifed in the semicolon-delimited list `<ids>`. Requires query string parameters
   `key` and `site`; has optional query string parameters `page` and `pagesize`.

## Download/install
 - `git clone` this repository (`https://github.com/SOBotics/apicache` or `git@github.com:SOBotics/apicache`).
 - Make sure you have an instance of [Redis](https://redis.io) running.
 - Modify `config.yml`, if necessary, to point to your instance of Redis.
 - Run the server with `python3 apicache.py`.
