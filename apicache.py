import json
import os.path
from flask import Flask, request, Response, render_template, abort, redirect
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


def items_response(items, has_more):
    resp = Response(json.dumps({'items': items, 'has_more': has_more}))
    resp.headers['Content-Type'] = 'application/json'
    return resp


def humanize(s):
    s = s.replace('/', ' - ')
    s = '.'.join(s.split('.')[0:-1])
    return s.title()


@app.route('/')
def index():
    return redirect('/docs/quickstart', code=302)


@app.route('/docs/<path:path>')
def docs(path):
    path = path + '.html'
    filepath = os.path.join(app.static_folder, 'docs', path)
    if os.path.isfile(filepath):
        with open(filepath, 'r') as f:
            content = f.read()

        return render_template('docs.html', content=content, title=humanize(path))
    else:
        abort(404)


@app.route('/questions/<ids>')
@app.route('/answers/<ids>')
@app.route('/posts/<ids>')
def posts_by_id(ids):
    page = int(request.args.get('page', 1))
    pagesize = int(request.args.get('pagesize', 10))
    site = request.args.get('site', None)
    key = request.args.get('key', None)
    max_age = int(request.args.get('max_age', 9e9))

    if site is None:
        return bad_param_error('site')
    if key is None:
        return bad_param_error('key')

    ids = ids.split(';')
    offset = (page - 1) * pagesize
    return_ids = ids[offset:offset + pagesize]

    full_posts = [json.loads(x.decode('utf-8')) for x in cache.get_post_set(ids, key, site, max_age=max_age)]
    return_posts = [x for x in full_posts if str(x['post_id']) in return_ids]

    return items_response(return_posts, len(full_posts) > page * pagesize)


@app.route('/questions')
def recent_questions():
    pagesize = int(request.args.get('pagesize', 10))
    site = request.args.get('site', None)
    key = request.args.get('key', None)
    max_age = int(request.args.get('max_age', 9e9))

    if site is None:
        return bad_param_error('site')
    if key is None:
        return bad_param_error('key')

    items = cache.get_recent_questions(key, site, max_age=max_age)[0:pagesize]
    return items_response(items, False)



if __name__ == '__main__':
    app.run()
