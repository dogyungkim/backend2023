from flask import Flask
from flask import request
from flask import make_response

app = Flask(__name__)

@app.route('/<arg1>/<op>/<arg2>')
def greet(arg1,op,arg2):
    x = int(arg1)
    y = int(arg2)
    if op ==  "+":
        return make_response(f'{x + y}', 200)
    elif op == "-":
        return make_response(f'{x - y}', 200)
    elif op == "*":
        return make_response(f'{x * y}', 200)
    else:
        return make_response(f'지원하지 않는 연산자', 400)


@app.route('/',methods=['GET','POST'])
def index():
    x = request.get_json().get('arg1','No value')
    y = request.get_json().get('arg2','No value')
    symbol = request.get_json().get('op','No OP')
    if symbol ==  "+":
        return make_response(f'{x + y}', 200)
    elif symbol == "-":
        return make_response(f'{x - y}', 200)
    elif symbol == "*":
        return make_response(f'{x * y}', 200)
    else:
        return make_response(f'지원하지 않는 연산자', 400)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=19106)