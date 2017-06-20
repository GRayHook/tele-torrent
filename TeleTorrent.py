# coding: utf-8
# Copyright © 2017 Marinkevich Sergey (G-Ray_Hook). All rights reserved.
# Licensed under GNU GPLv2 (look at file named 'LICENSE')
"""sss"""
import urllib2
import base64
import json
import time

# Constants for requests to uTorrent
USERNAME = 'gray'
PASSWORD = '@cjcyb@EUKZ2'
REQUEST_URL = 'http://192.168.1.219:8080/gui/'

# Constants for indexes uTorrent's list of torrents
TR_HASH = 0
TR_STATUS = 1
TR_NAME = 2
TR_PROGRESS = 4

# Constants for requests to Telegram
TG_TOKEN = '435150189:AAHEcUokmbFmqhdec8dQl88KdjD_eKqpRi8'
TG_LINK = 'https://api.telegram.org/bot' + TG_TOKEN + '/'

def main():
    """Body of program"""
    watchins = []
    while True:
        guid, token = get_data()
        torrents = json.loads(get_list(guid, token))[u'torrents']
        for torrent in torrents:
            if torrent[TR_PROGRESS] == 1000:
                if watchins.__contains__(torrent[TR_HASH]):
                    send_torrent(torrent[TR_NAME])
            else:
                if not watchins.__contains__(torrent[TR_HASH]):
                    watchins += [torrent[TR_HASH]]
        time.sleep(7)

def tg_get_msgs(cur_msg):
    """Getting list of messages from Telegram chats.
    cur_msg — last message, that have been getting from chats, + 1"""
    request_string = TG_LINK + 'getUpdates?offset=' + str(cur_msg)
    response = urllib2.urlopen(request_string)
    results = json.loads(response.read())[u'result']
    last = False
    for result in results:
        last = result[u'update_id']
        tg_handler(result[u'message'])
    # Drop readed messages from Telegram server:
    if last:
        request_string = TG_LINK + 'getUpdates?offset=' + str(last + 1)
        urllib2.urlopen(request_string)

def tg_handler(message):
    """Handler for incoming messages from Telegram"""
    print message

def send_torrent(msg):
    """Sending message via Telegram"""
    print 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA', msg

def get_list(guid, token):
    """Getting list of torrents"""
    request = auth_request(REQUEST_URL + '?token=' + token + '&list=1')
    request.add_header("Cookie", "GUID=%s;" % guid)
    response = urllib2.urlopen(request)
    return response.read()

def get_data():
    """Getting data(guid, token) from uTorrent by http"""
    request = auth_request(REQUEST_URL + 'token.html')
    response = urllib2.urlopen(request)
    headers = response.headers.items()
    guid = get_cooka(headers, 'GUID')
    token = get_divka(response.read(), 'token')
    return guid, token

def auth_request(url):
    """Authorized request (by CONSTS in a begining of code)"""
    request = urllib2.Request(url)
    base64string = base64.encodestring('%s:%s' % (USERNAME, PASSWORD))
    base64string = base64string.replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)
    return request

def get_divka(str4ka, key):
    """Parse substring from str4ka - html's tag 'div' with id='key'"""
    start = str4ka.find('>', str4ka.find("id='" + key + "'")) + 1
    end = str4ka.find('</div>', start)
    return str4ka[start:end]

def get_cooka(headers, key):
    """Getting cookie('set-cookie' header) by key from headers"""
    for header in headers:
        if header[0] == 'set-cookie':
            cookies = header[1]
            try:
                start = cookies.index(key + '=') + len(key) + 1
            except ValueError:
                print 'Key not founded!'
            end = cookies.find(';', start)
            return cookies[start:end]

if __name__ == '__main__':
    main()
