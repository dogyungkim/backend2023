
def application(environ, start_response):
    print(environ['REQUEST_METHOD'])
    print(environ['PATH_INFO'])

    status = '200 OK'
    headers = [('Content- Type', 'text/html')]

    start_response(status, headers)

    return [b'Hello World']