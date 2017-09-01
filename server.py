from halibot import HalAgent, HalConfigurer, Message
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import ssl, socket

version = '1.0.0'

class Handler(BaseHTTPRequestHandler):

    server_version = 'halibot/0 http/' + version

    # We override this because we want to control how we dispatch based on the
    # method.
    def handle_one_request(self):
        print('handle_one_request entry')
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                # An error code has been sent, just exit
                return

            # Get the body
            bodylen = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(bodylen)

            # Make the message to send
            author = self.client_address[0] + ':' + str(self.client_address[1])
            msg = Message(body=body, author=author, origin=self.server.agent.name)
            msg.type = 'http'
            msg.http = {
                    'command': self.command,
                    'path': self.path,
                    'request_version': self.request_version,
                    'requestline': self.requestline,
                    'headers': self.headers,
            }

            ## Get what destinations we want to send to
            out = self.server.agent.config.get('out')
            if out:
                dests = out.get(self.command)
                if not dests:
                    self.send_error( HTTPStatus.NOT_IMPLEMENTED
                                   , 'Unsupported method (%r)' % self.command
                                   )
                    return
            else:
                dests = self.server.agent._hal.objects.modules.keys()

            results = self.server.agent.sync_send_to(msg, dests)
            result_msgs = []
            content = ''
            code = 204

            for r in results.values():
                for m in r:
                    if m.type == 'error':
                        # Module signaled that there was an error
                        self.send_error(m.code, m.body)
                        return
                    code = 200
                    content += m.body + '\n'
            content = content.encode()

            # Everything is good
            self.send_response(code)
            if code == 200: self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
            self.wfile.flush()
        except socket.timeout as e:
            #a read or a write timed out.Discard this connection
            self.log_error('Request timed out: %r', e)
            self.close_connection = True
            return


class Server(HalAgent):

    class Configurer(HalConfigurer):
        def configure(self):
            self.optionString('hostname', prompt='Hostname', default='')
            self.optionInt('port', prompt='Port', default=8000)
            self.optionString('keyfile', prompt='SSL key file')
            self.optionString('certfile', prompt='SSL certificate file')

    def init(self):
        self.server_thread = Thread(target=self.serve)
        self.server_thread.start()

    def shutdown(self):
        self.server.shutdown()
        self.server_thread.join()

    def serve(self):
        addr = (self.config['hostname'], self.config['port'])
        keyfile = self.config.get('keyfile')
        certfile = self.config.get('certfile')

        self.server = HTTPServer(addr, Handler)
        self.server.agent = self
        if keyfile:
            self.server.socker = ssl.wrap_socket( self.server.socket
                                                , keyfile=keyfile
                                                , certfile=certfile
                                                , server_side=True
                                                )
        self.server.serve_forever()

