#!/usr/bin/env python

#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# Authors: Caner Candan <caner@candan.fr>
#

"""A script to easily activate proxy ports
"""

__author__      = 'Caner Candan'
__version__     = '1.0'


############################
# gate breaker configuration
############################

SERVER_USERNAME = 'root'        ### Please define the SSH username
SERVER_HOST = '127.0.0.1'       ### Please enter your server ip address used like ssh tunnel
SERVER_PORT = '443'             ### And now the SSH port

RUN_PATH = './run'

############################


############################
# LOGGER
############################

import logging

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

def logger(level_name, filename='gatebreaker.log'):
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        filename=filename, filemode='a'
        )

    console = logging.StreamHandler()
    console.setLevel(LEVELS.get(level_name, logging.NOTSET))
    console.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
    logging.getLogger('').addHandler(console)

############################


############################
# PARSER
############################

import optparse

def parser(parser=optparse.OptionParser()):
    parser.add_option('-v', '--verbose', choices=LEVELS.keys(), default='info', help='set a verbose level')
    parser.add_option('-o', '--output', help='give an output filename for logging', default='gatebreaker.log')

    parser.add_option('-l', '--list', help='give a file path containing the list of ports you want to use', default='')
    parser.add_option('-p', '--port', help='give a specific port number', default='')

    parser.add_option('-s', '--start', action='store_true', help='start the given port number process or all gate breaker processes', default=False)
    parser.add_option('-r', '--restart', action='store_true', help='restart the given port number process or all gate breaker processes', default=False)
    parser.add_option('-k', '--kill', action='store_true', help='kill the given port number process or all gate breaker processes', default=False)
    parser.add_option('-m', '--monitor', action='store_true', help='check the status for the given port number process or all gate breaker processes', default=False)
    parser.add_option('-a', '--available', action='store_true', help='give the list of all ports that you can activate from the given list file', default=True)

    parser.add_option('-V', '--version', action='store_true', help='current version', default=False)

    options, args = parser.parse_args()

    logger(options.verbose, options.output)

    return options

options = parser()

############################


############################
# GateBreaker begins
############################

import sys, os, subprocess

def getrunfiles():
    filelist = []

    try:
        filelist = os.listdir(RUN_PATH)
    except OSError, e:
        logging.error(e)

    return filelist

def kill(port=options.port):
    if port == '': return

    logger = logging.getLogger('kill(%s)' % port)

    logger.debug('killing...')

    try:
        path = '%s/%s' % (RUN_PATH, port)
        pid = int(open(path).readline())
        logger.debug('pid to kill: %s', pid)

        try:
            os.kill(pid, 2)
        except OSError, e:
            logger.error(e)

        try:
            os.unlink(path)
        except OSError, e:
            logger.error(e)

        logger.debug('done')

    except IOError, e:
        logger.error(e)

def killall():
    if not options.kill: return

    for x in getrunfiles():
        kill(x)

def monitor(port=options.port):
    if port == '': return

    logger = logging.getLogger('monitor(%s)' % port)

    try:
        path = '%s/%s' % (RUN_PATH, port)
        pid = int(open(path).readline())
        logger.debug('pid to check: %s', pid)
        os.getsid(pid)
        logger.info('pid %d seems ok' % pid)
    except IOError, e:
        logger.error(e)
    except OSError, e:
        logger.error(e)

def monitorall():
    if not options.monitor: return

    for x in getrunfiles():
        monitor(x)

def start(ports, port=options.port):
    logger = logging.getLogger('start(%s)' % port)

    logger.debug('starting...')

    if int(port) not in ports:
        logger.info('%s not available in the list' % port)
        return

    exist = True
    try:
        path = '%s/%s' % (RUN_PATH, port)
        open(path)
        logger.warning('port already activated')
    except IOError:
        exist = False

    if exist: return

    mode, remotehost, remoteport, description = ports[int(port)]

    pid = subprocess.Popen(['autossh',
                            '-M', '0', '-N',
                            '-p', SERVER_PORT, '%s@%s' % (SERVER_USERNAME, SERVER_HOST),
                            '-R' if mode == 'IN' else '-L',
                            '*:%s:%s:%s' % (port, remotehost, remoteport)
                            ]).pid

    logger.debug('pid = %d', pid)
    logger.debug('port number = %s', port)

    try:
        os.mkdir(RUN_PATH)
    except OSError, e:
        logger.info(e)

    open('%s/%s' % (RUN_PATH, port), 'w').write(str(pid))

    logger.debug('done')

def restart(ports, port=options.port):
    if port == '': return

    logger = logging.getLogger('restart(%s)' % port)

    logger.debug('restarting...')

    if int(port) not in ports:
        logger.info('%s not available in the list' % port)
        return

    kill(port)
    start(ports, port)

    logger.debug('done')

def available(ports, port=options.port):
    logger = logging.getLogger('available(%s)' % port)

    logger.debug('availability...')

    if int(port) not in ports:
        logger.info('%s not available in the list' % port)
        return

    mode, remotehost, remoteport, description = ports[int(port)]

    logger.info('\t%s,\t%s,\t%s,\t\t\t%s,\t%s' % (port, mode, remotehost, remoteport, description))

    logger.debug('done')

def applytoall(ports, fct):
    for port in ports.iterkeys():
        fct(ports, port)

if __name__ == '__main__':

    if options.version:
        logging.info('VERSION: %s', __version__)

    if options.kill:
        if options.port == '':
            killall() # with -k
        else:
            kill() # with -k and -p PORT
        sys.exit()

    if options.monitor:
        if options.port == '':
            monitorall() # with -m
        else:
            monitor() # with -m and -p PORT
        sys.exit()

    if options.list == '': sys.exit()

    # with -l FILE_PATH

    ports = eval(''.join(open(options.list).readlines()))

    if options.restart:
        if options.port == '':
            applytoall(ports, restart) # with -r
        else:
            restart(ports) # with -r and -p PORT
        sys.exit()

    if options.start:
        if options.port == '':
            applytoall(ports, start) # with -s
        else:
            start(ports) # with -s and -p PORT

    if options.available:
        if options.port == '':
            applytoall(ports, available) # with -a
        else:
            available(ports) # with -a and -p PORT

############################
