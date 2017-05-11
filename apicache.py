from flask import Flask
import yaml
from cache import Cache


app = Flask(__name__)
with open('config.yml', 'r', encoding='utf-8') as f:
    config = yaml.load(f)

cache = Cache(config)


@app.route('/')
def index():
    # Eventually, this should probably redirect to apicache's documentation.
    return 'apicache'


if __name__ == '__main__':
    app.run()
