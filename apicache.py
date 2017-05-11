import json
from flask import Flask, request, Response
import yaml
from cache import Cache


app = Flask(__name__)
with open('config.yml', 'r', encoding='utf-8') as f:
    config = yaml.load(f)

cache = Cache(config)


def bad_param_error(param):
    resp = Response(json.dumps({'error_id': 400, 'error_message': '{} is required'.format(param),
                                'error_name': 'bad_parameter'}))
    resp.headers['Content-Type'] = 'application/json'
    return resp


@app.route('/')
def index():
    # Eventually, this should probably redirect to apicache's documentation.
    return 'apicache'


@app.route('/questions/<ids>')
@app.route('/answers/<ids>')
@app.route('/posts/<ids>')
def posts_by_id(ids):
    page = request.args.get('page', 1)
    pagesize = request.args.get('pagesize', 10)
    site = request.args.get('site', None)
    key = request.args.get('key', None)
    if site is None:
        return bad_param_error('site')
    if key is None:
        return bad_param_error('key')

    ids = ids.split(';')
    offset = (page - 1) * pagesize
    return_ids = ids[offset:offset + pagesize]

    full_posts = [json.loads(x.decode('utf-8')) for x in cache.get_post_set(ids, key, site)]
    return_posts = [x for x in full_posts if str(x['post_id']) in return_ids]
    resp = Response(json.dumps({'items': return_posts, 'has_more': len(full_posts) > len(return_posts)}))
    resp.headers['Content-Type'] = 'application/json'
    return resp



if __name__ == '__main__':
    app.run()
