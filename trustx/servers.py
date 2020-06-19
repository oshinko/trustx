import argparse
import wsgiref.simple_server


class WSGI:
    statuses = {int(x.split(maxsplit=1)[0]): x.split(maxsplit=1)[1]
                for x in """
200 OK
302 Found
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
405 Method Not Allowed
""".strip().splitlines()}

    default_headers = [('Access-Control-Allow-Origin', '*')]

    def __init__(self):
        self._handlers = []

    def _respond(self, respond, status, headers=None):
        respond(f'{status} {self.statuses[status]}',
                self.default_headers + (headers or []))

    def __call__(self, environ, respond):
        for route, f, options in self._handlers:
            if route == environ['PATH_INFO']:
                resp = f()
                self._respond(respond, 200)
                return [resp.encode()]
        self._respond(respond, 404)
        return []

    def route(self, route, **options):
        def decorator(f):
            self._handlers.append((route, f, options))
            return f
        return decorator


wsgi = WSGI()


@wsgi.route('/', method='GET')
def index():
    return 'Hello!'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='type', required=True)
    subparser = subparsers.add_parser('wsgi')
    subparser.add_argument('--port', default=8000)
    args = parser.parse_args()
    if args.type == 'wsgi':
        with wsgiref.simple_server.make_server('', args.port, wsgi) as httpd:
            print(f'Serving HTTP on port {args.port}, control-C to stop')
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print('Shutting down.')
