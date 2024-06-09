from http import HTTPStatus
import random
import redis
import requests
import json
import urllib

from flask import abort, Flask, make_response, render_template, Response, redirect, request

app = Flask(__name__)

db = redis.Redis(host='', port = , db = 0)


naver_client_id = ''
naver_client_secret = ''
naver_redirect_uri = 'http://localhost:80/auth'


@app.route('/')
def home():

    userId = request.cookies.get('userId', default=None)
    
    #userId 로부터 DB 에서 사용자 이름을 얻어오는 코드
    if not userId:
        #cookie에 userID가 없을 때
        name = None
    else:
        name = db.get(userId).decode('utf-8')


    # 이제 클라에게 전송해 줄 index.html 을 생성한다.
    # template 로부터 받아와서 name 변수 값만 교체해준다.
    return render_template('index.html', name=name)


@app.route('/login')
def onLogin():
    params={
            'response_type': 'code',
            'client_id': naver_client_id,
            'redirect_uri': naver_redirect_uri,
            'state': random.randint(0, 10000)
        }
    urlencoded = urllib.parse.urlencode(params)
    url = f'https://nid.naver.com/oauth2.0/authorize?{urlencoded}'
    return redirect(url)



@app.route('/auth')
def onOAuthAuthorizationCodeRedirected():
    # TODO: 아래 1 ~ 4 를 채워 넣으시오.

    # 1. redirect uri 를 호출한 request 로부터 authorization code 와 state 정보를 얻어낸다.
    authCode = request.args['code']
    state = request.args['state']


    # 2. authorization code 로부터 access token 을 얻어내는 네이버 API 를 호출한다.
    params={
            'grant_type': 'authorization_code',
            'client_id': naver_client_id,
            'client_secret': naver_client_secret,
            'code': authCode,
            'state' : state
        }
    urlencoded = urllib.parse.urlencode(params)
    url = f'https://nid.naver.com/oauth2.0/token?{urlencoded}'
    token_request = requests.get(url).json()

    access_token = token_request.get("access_token")


    # 3. 얻어낸 access token 을 이용해서 프로필 정보를 반환하는 API 를 호출하고,
    #    유저의 고유 식별 번호를 얻어낸다.
    header = "Bearer " + access_token  
    url = "https://openapi.naver.com/v1/nid/me"
    id_request = urllib.request.Request(url)
    id_request.add_header("Authorization", header)
    response = urllib.request.urlopen(id_request)
    rescode = response.getcode()
    if(rescode==200):
        response_body = response.read().decode('utf-8')
        buffer = json.loads(response_body)
        user_info = buffer['response']
    else:
        print("Error Code:" + rescode) 


    # 4. 얻어낸 user id 와 name 을 DB 에 저장한다.
    user_id = user_info['id']
    user_name = user_info['name']

    db.set(user_id,user_name)


    # 5. 첫 페이지로 redirect 하는데 로그인 쿠키를 설정하고 보내준다.
    response = redirect('/')
    response.set_cookie('userId', user_id)

    return response


@app.route('/memo', methods=['GET'])
def get_memos():
    # 로그인이 안되어 있다면 로그인 하도록 첫 페이지로 redirect 해준다.
    userId = request.cookies.get('userId', default=None)
    if not userId:
        return redirect('/')

    # DB 에서 해당 userId 의 메모들을 읽어온다
    result = []

    text_list = db.lrange(db.get(userId),0,-1)
    for text in text_list:
        result.append(json.loads(text))
    
    # memos라는 키 값으로 메모 목록 보내주기
    return {'memos': result}


@app.route('/memo', methods=['POST'])
def post_new_memo():
    # 로그인이 안되어 있다면 로그인 하도록 첫 페이지로 redirect 해준다.
    userId = request.cookies.get('userId', default=None)
    if not userId:
        return redirect('/')

    # 클라이언트로부터 JSON 을 받았어야 한다.
    if not request.is_json:
        abort(HTTPStatus.BAD_REQUEST)

    #클라이언트로부터 받은 JSON 에서 메모 내용을 추출한 후 DB에 userId 의 메모로 추가한다.
    text = json.loads(request.data)['text']

    # UserName으로 DB에 메모 저장
    data = {
        'text' : text
    }

    db.rpush(db.get(userId),json.dumps(data))

    #
    return '', HTTPStatus.OK

#AWS 상태 검사 용 
@app.route('/health', methods=['GET'])
def health_check():
    return '',HTTPStatus.OK

if __name__ == '__main__':
    app.run('0.0.0.0', port=80, debug=True)
