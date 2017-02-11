import asyncio
import os
import logging
import json
import sys
import sqlite3
from aiohttp import web

import configargparse

log = logging.Logger(name="server")
PAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                         "page")


def init_db(db_file):
    """initialize the database

    Configure the database if necessary

    :param db_file: path to the database
    :type db_file: str

    """
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    cur.executescript('CREATE TABLE IF NOT EXISTS users '
                      '(id TEXT PRIMARY KEY, subinfo TEXT);')
    con.commit()
    con.close()


def setup(sysargs):
    """Read in the args

    :param sysargs: System arguments
    :type sysargs: dict

    :returns: the settings object and parser

    """
    parser = configargparse.ArgumentParser(
        default_config_files=["push_server.ini"],
    )
    parser.add_argument('--config',
                        help='Common configuration file path',
                        dest='config_file', is_config_file=True)
    parser.add_argument('--debug', '-d',
                        help="Debug info",
                        default=False,
                        action="store_true")
    parser.add_argument('--port', '-p',
                        help="Port to monitor",
                        default=8200, type=int)
    parser.add_argument('--db',
                        help='Path to SQLite3 database',
                        dest="db_path",
                        default='users.db', type=str)
    args = parser.parse_args(sysargs)
    init_db(args.db_path)
    return args, parser


CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST",
    "Access-Control-Allow-Headers": ",".join(["content-type"]),
    "Access-Control-Expose-Headers": ",".join(["content-type"])
}


def index(request):
    """If requested, display the 'index' page.

    Additional processing could be done here. This is more a stub
    function than anything else.

    :param request: Incoming request object
    :type request: web.Request

    :returns: a Response containing the index file.

    """
    file = open(os.path.join(PAGE_PATH, "index.html"), "r")
    headers = CORS_HEADERS.copy()
    headers["content-type"] = "text/html"
    return web.Response(text="".join(file.readlines()),
                        headers=headers)


@asyncio.coroutine
def store_user(args, user_info):
    """Store the user subscription data to the database

    :param args: Settings
    :type args: object
    :param user_info: Subscription Info block
    :type user_info: dict

    """
    db = sqlite3.connect(args.db_path)
    cur = db.cursor()
    # if the client didn't send a userid, we'll fake one from the endpoint
    # because that's what the matching javascript would have done.
    # You should probably have a real ID tied to a real user record.
    if "id" not in user_info:
        user_info["id"] = user_info["endpoint"][-8:]
    id = str(user_info.pop("id"))
    cur.execute("insert into users values (?,?)",
                (id, json.dumps(user_info)))
    db.commit()
    db.close()


def register(request):
    """Handle registration POST message

    :param request: Incoming request object
    :type request: web.Request

    :returns: a Response containing the registration response

    """
    try:
        # Extract the JSON body out of the request.
        body = yield from request.json()
        if not isinstance(body, dict):
            raise Exception("body not recognized")
        yield from store_user(request.app['config'], body)
    except sqlite3.IntegrityError as ex:
        log.warning("Already registered. ignoring")
        return web.Response(text="already registered", status=200)
    except Exception as e:
        log.error(
            "### ERROR: Could not process registration: {}".format(repr(e))
        )
        return web.Response(text="Error: {}".format(str(e)), status=500)
    return web.Response(text="registering", status=201)


def main(sysargs=None):
    if not sysargs:
        sysargs = sys.argv[1:]
    args, parser = setup(sysargs)
    loop = asyncio.get_event_loop()
    if args.debug:
        loop.set_debug(enabled=True)
        logging.basicConfig(level=logging.DEBUG)
    app = web.Application(loop=loop)
    app['config'] = args
    # Static files are "served" from this virtual directory.
    # A secure server would probably put them in a different directory.
    app.router.add_static('/i/',
                          path=PAGE_PATH,
                          name='static')
    app.router.add_get('/', index)
    app.router.add_post('/', register)
    web.run_app(app,
                host='0.0.0.0',
                port=args.port)


if __name__ == '__main__':
    main(sys.argv[1:])
