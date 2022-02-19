#! /usr/bin/env python3

import sys
import os
import pprint
import json
import requests
import random
import urllib3
import textwrap
import logging
import argparse


###############################################################################
program_name = os.path.basename(__file__)
VERSION = 0.2
logger = logging.getLogger(__name__)


###############################################################################
class ArgumentParser(argparse.ArgumentParser):

    def error(self, message):
        print('\n\033[1;33mError: {}\x1b[0m\n'.format(message))
        self.print_help(sys.stderr)
        # self.exit(2, '%s: error: %s\n' % (self.prog, message))
        self.exit(2)

    # def format_usage(self):
    #     usage = super()
    #     return "CUSTOM"+usage


# ------------------------------------------------------------------------------
def parser_add_arguments():
    """
        Parse comamnd line parameters
    """
    parser = ArgumentParser(
        prog=program_name,
        description=textwrap.dedent('''\
                        Utility for ingesting fingerprints into a DDoSDB instance

                        '''),
        formatter_class=argparse.RawTextHelpFormatter, )

    parser.add_argument("filename",
                        metavar='{file|dir}',
                        help=textwrap.dedent('''\
                        The (json) fingerprint file, or a directory containing fingerprint files.
                        In case of a directory, every json file in that directory is expected
                        to be a fingerprint
                        '''),
                        action="store",
                        )

    parser.add_argument("url",
                        metavar='{DDoSDB URL}',
                        help=textwrap.dedent('''\
                        The base URL of the DDoSDB instance, e.g. https://ddosdb.org
                        '''),
                        action="store",
                        )

    parser.add_argument("token",
                        metavar='{Token}',
                        help=textwrap.dedent('''\
                        The Authorization Token to use. This should be of a DDoSDB account with
                        the permissions to add/upload a fingerprint.
                        '''),
                        action="store",
                        )

    parser.add_argument("-n",
                        help=textwrap.dedent('''\
                        Ingest each fingerprint <n> times, with 1 being the default.
                        If N>1 then random keys are used for each time the fingerprint is
                        uploaded, rather than the key present in the fingerprint itself.
                        '''),
                        action="store",
                        type=int,
                        default=1)

    parser.add_argument("-c", "--verify",
                        help="Check the server certificate in case of an https URL",
                        action="store_true")

    parser.add_argument("-v", "--verbose",
                        help="more verbose output",
                        action="store_true")
    parser.add_argument("--debug",
                        help="show debug output",
                        action="store_true")
    parser.add_argument("-V", "--version",
                        help="print version and exit",
                        action="version",
                        version='%(prog)s (version {})'.format(VERSION))

    return parser


# ------------------------------------------------------------------------------
class CustomConsoleFormatter(logging.Formatter):
    """
        Log facility format
    """

    def format(self, record):
        info = '\033[0;32m'
        # info = '\t'
        warning = '\033[0;33m'
        error = '\033[1;33m'
        debug = '\033[1;34m'
        reset = "\x1b[0m"

        formatter = '%(levelname)s [%(filename)s.py:%(lineno)s/%(funcName)s] %(message)s'
        if record.levelno == logging.INFO:
            log_fmt = info + '%(message)s' + reset
            self._style._fmt = log_fmt
        elif record.levelno == logging.WARNING:
            log_fmt = warning + formatter + reset
            self._style._fmt = log_fmt
        elif record.levelno == logging.ERROR:
            log_fmt = error + formatter + reset
            self._style._fmt = log_fmt
        elif record.levelno == logging.DEBUG:
            log_fmt = debug + formatter + reset
            self._style._fmt = log_fmt
        else:
            self._style._fmt = formatter

        return super().format(record)


# ------------------------------------------------------------------------------
def get_logger(args):
    logger = logging.getLogger(__name__)

    # Create handlers
    console_handler = logging.StreamHandler()
    #    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = CustomConsoleFormatter()
    console_handler.setFormatter(formatter)

    if args.verbose:
        logger.setLevel(logging.INFO)

    if args.debug:
        logger.setLevel(logging.DEBUG)

    # add handlers to the logger
    logger.addHandler(console_handler)

    return logger


# ------------------------------------------------------------------------------
def openJSON(filename):
    """open the JSON (result) file and return it as a json structure"""
    data = {}
    with open(filename) as f:
        data = json.load(f)
    return data

###############################################################################
def main():

    global VERBOSE, DEBUG, logger

    parser = parser_add_arguments()
    args = parser.parse_args()
    VERBOSE = args.verbose
    DEBUG = args.debug
    logger = get_logger(args)
    pp = pprint.PrettyPrinter(indent=4)

    filename = args.filename
    filelist = []

    if os.path.isdir(filename):
        logger.debug("Provided filename is a directory")
        if not filename.endswith("/"):
            filename = filename + '/'
        with os.scandir(filename) as it:
            for entry in it:
                if not entry.name.startswith('.') and entry.is_file() and entry.name.endswith('.json'):
                    filelist.append('{0}{1}'.format(filename, entry.name))
    else:
        logger.debug("Provided filename is a fingerprint")
        filelist.append(filename)

    logger.info("Fingerprints to process: {}".format(filelist))

    for fn in filelist:
        print('Fingerprint file {}'.format(fn))
        data = openJSON(fn)
        #    pp.pprint(data)
        if 'key' in data:
            print('Fingerprint key={}'.format(data['key']))
            try:
                # if args.n > 1:
                #     data['key'] = "".join([random.choice("abcdef0123456789") for i in range(15)])
                for i in range(0, args.n):
                    print("\tUploading fingerprint {}: key={} response=".format(i, data['key']), end='')
                    # urllib3.disable_warnings()
                    r = requests.post("{}/api/fingerprint/".format(args.url),
                                      headers={'Authorization': 'Token {}'.format(args.token)},
                                      json=data,
                                      timeout=10,
                                      verify=args.verify)
                    print(r.status_code)
                    data['key'] = "".join([random.choice("abcdef0123456789") for i in range(15)])
            except Exception as e:
                logger.error(e)
                continue


if __name__ == '__main__':
    # Run the main process
    main()


