import sys
import json
import requests
import sqlite3
import logging
import asyncio

import configargparse
from pywebpush import WebPusher

log = logging.Logger(name="pusher")


def setup(sysargs):
    """Read in the arguments and configure things for startup.

    :param sysargs: List of system arguments
    :type sysargs: dict

    :returns: an namespace object containing the argument settings
    :return type: object

    """
    parser = configargparse.ArgumentParser(
        default_config_files=["push_server.ini"],
    )
    parser.add_argument('--config', help='Common configuration file path',
                        dest='config_file', is_config_file=True)
    parser.add_argument('--debug', '-d', help="Debug info", default=False,
                        action="store_true")
    parser.add_argument('--db', help='Credential database path',
                        dest="db_path", default='users.db', type=str)
    parser.add_argument('--topic', help='Message topic', default=None,
                        type=str)
    parser.add_argument('--ttl', help='Message time to live', default=300,
                        type=int)
    parser.add_argument('--id', help="User ID to send to", default="",
                        type=str)
    parser.add_argument('--msg', help='message body to send', default=None,
                        type=str, required=True)
    args = parser.parse_args(sysargs)
    args.db = sqlite3.connect(args.db_path)
    args.db.row_factory = sqlite3.Row
    if args.debug:
        log.setLevel(logging.INFO)
    return args


def get_users(args):
    """Fetch the users from the database.

    Will fetch all users, unless 'id' is defined, then will attempt to
    find all matching users. This uses SQL's standard similarity match.

    :param args: settings
    :type args: object

    :returns: list of sqlite3.Row object containing matching users.

    """
    cur = args.db.cursor()
    cur.execute(
        "select * from users where id like '%{}%'".format(args.id))
    return cur.fetchall()


async def drop_user(args, user):
    """Remove a user from the database

    :param args: settings
    :type args: object
    :param user: UserID to remove
    :type user: str

    """
    log.warn("Dropping no longer valid user: {}".format(user))
    cur = args.db.cursor()
    cur.execute("delete from users where id=?", (user,))


async def process_user(user, args, headers):
    """Send a message to a user or drop the user if no longer valid.

    :param user: UserID of customer to attempt to send Subscription Update
    :type user: string
    :param args: settings
    :type args: object
    :param headers: Additional headers to send
    :type headers: dict

    :returns: UserID of failed sends

    """
    sub_info = json.loads(user["subinfo"])
    try:
        result = WebPusher(sub_info).send(
            args.msg,
            headers=headers,
            ttl=args.ttl)
        print("Result: {}".format(result.status_code))
        if result.status_code > requests.codes.ok:
            # Remove any users that no longer want updates.
            if result.status_code in [404, 410]:
                try:
                    reply = json.loads(result.text)
                    reason = reply.get(
                        "message",
                        "Unknown reason")
                    if 'more_info' in reply:
                        reason += (
                            "\nFor more info, see: " +
                            reply['more_info']
                            )
                except:
                    reason = "and couldn't understand {}".format(
                        result.text
                        )
                log.error(
                    "Failed to send to {}: {}".format(
                        user["id"],
                        reason,

                    )
                )
                await drop_user(args, user["id"])
                args.db.commit()
                return None
            result.raise_for_status()
        log.info("Sent message to {}".format(user["id"]))
        return None
    except Exception as x:
        log.error("Could not process user {}".format(repr(x)))
        return user["id"]


async def process_users(args, headers):
    """get the list of users, then process each in it's own thread

    :param args: settings
    :type args: object
    :param headers: additional headers to send
    :type headers: dict

    """
    try:
        # Since this is the data fetch, and the process shouldn't continue
        # without it, block on getting the user list.
        # There are ways to make this faster, but this is just a demo app.
        users = get_users(args)
        if len(users) == 0:
            log.error("No users found. No messages being sent.")
            return
        log.info("Processing message for {} users".format(len(users)))
        # generate the list of future functions to be called by gather.
        futures = [process_user(user, args, headers) for user in users]
        # pass these out to threads and gather the results.
        results = await asyncio.gather(*futures, return_exceptions=True)
        for result in results:
            if result is not None:
                print("Removed currently invalid users: {}".format(
                    result))
    except Exception as x:
        log.error("Could not send message: {}".format(repr(x)))


def main(sysargs=None):
    if not sysargs:
        sysargs = sys.argv[1:]
    args = setup(sysargs)
    headers = {}
    if args.topic:
        if ' ' in args.topic or '"' in args.topic or '"' in args.topic:
            raise Exception("don't use quotes or spaces in your topics")
        topic = args.topic.strip('"\'')
        # The only thing that separates a subscription update from a
        # topic update, is a header.
        headers = {"topic": topic}

    # process all users in a thread.
    loop = asyncio.get_event_loop()
    if args.debug:
        loop.set_debug(enabled=True)
        logging.basicConfig(level=logging.DEBUG)
    loop.run_until_complete(process_users(args, headers))


if __name__ == '__main__':
    main(sys.argv[1:])
