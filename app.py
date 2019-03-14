import os
import tornado.httpserver
import tornado.ioloop
import tornado.web
from src import log
from src.handler import CompeChatHandler
import configparser

inifile = configparser.ConfigParser()
inifile.read('./config.ini', 'UTF-8')

def main():
    log.setting()
    app = tornado.web.Application(
        [
            ('/CompeChat', CompeChatHandler),
            (r'/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(os.path.dirname(__file__), "static")}),
        ])
    server = tornado.httpserver.HTTPServer(app)
    server.listen(inifile.get('settings', 'port'))
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
