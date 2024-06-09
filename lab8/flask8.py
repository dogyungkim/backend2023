from flask import Flask
from flask import request


app = Flask(__name__)


@app.route('/',methods=['GET','POST'])
def index():
    return {
        'mehtod' : request.method,
        'name' : request.args.get('name',default='이름이 없는자'),
        'client' : request.headers['User-Agent'],
        'key1' : request.get_json().get('key1','No key')
    }


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=19106)