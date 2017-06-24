# coding: utf-8
# Copyright © 2017 Marinkevich Sergey (G-Ray_Hook). All rights reserved.
# Licensed under GNU GPLv2 (look at file named 'LICENSE')
# Contact: s@marinkevich.ru
"""uTorrent notification for Telegram"""
import urllib2
import base64
import json
import time
import threading

# Files's constants
FILE_SETTINGS = 'settings'

# Constants for indexes uTorrent's list of torrents
TR_HASH = 0
TR_STATUS = 1
TR_NAME = 2
TR_PROGRESS = 4

# Constants for requests to Telegram
TG_TOKEN = 'PLACE_YOUR_TOKEN'
TG_LINK = 'https://api.telegram.org/bot' + TG_TOKEN + '/'

def main():
    """Body of program"""
    try:
        tr_evnt = threading.Event()
        tg_evnt = threading.Event()
        utor_thread = threading.Thread(target=tr_thread,
                                       args=[tr_evnt],
                                       name='uTorrent')
        tgram_thread = threading.Thread(target=tg_thread,
                                        args=[tg_evnt],
                                        name='Telegram')
        utor_thread.start()
        tgram_thread.start()
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print "\nWaiting for threads"
        tr_evnt.set()
        tg_evnt.set()
        utor_thread.join()
        tgram_thread.join()
        print "Threads closed"

def tr_thread(evnt):
    """Target for uTorrent's thread"""
    watchins = []
    while not evnt.is_set():
        try:
            settings = file(FILE_SETTINGS, 'r')
            setts = json.load(settings)
            settings.close()
        except IOError:
            setts = {}
        for sett in setts:
            try:
                guid, token = get_data(setts[sett])
                torrents = json.loads(get_list(guid,
                                               token,
                                               setts[sett]))[u'torrents']
            except urllib2.HTTPError:
                torrents = []
            except urllib2.URLError:
                torrents = []
            for torrent in torrents:
                if torrent[TR_PROGRESS] == 1000:
                    if watchins.__contains__(torrent[TR_HASH]):
                        del watchins[watchins.index(torrent[TR_HASH])]
                        text = 'Your .torrent named "' + torrent[TR_NAME] + \
                               '" have been downloaded successful'
                        tg_send(sett, text)
                else:
                    if not watchins.__contains__(torrent[TR_HASH]):
                        watchins += [torrent[TR_HASH]]
        time.sleep(7)

def tg_thread(evnt):
    """Thread for Telegram bot daemon"""
    while not evnt.is_set():
        tg_get_msgs()
        time.sleep(2)

def tg_get_msgs():
    """Getting list of messages from Telegram chats"""
    request_string = TG_LINK + 'getUpdates?offset=2'
    try:
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
    except urllib2.HTTPError:
        print 'alarma 404'

def tg_handler(message):
    """Handler for incoming messages from Telegram"""
    txt = message['text']
    command = txt.split()
    TG_FUNS.get(command[0], tg_msg_hz)(message)

def tg_msg_hz(message):
    """For unknown cases of reiceved messages"""
    print 'called hz\n', message['text']
    tg_send(message['chat']['id'], 'I don\'t understand you')

def tg_msg_reg(message):
    """Adding ip, uname, passwd to conf-file"""
    print 'called reg\n', message, '\n'
    args = message[u'text'].split()[1:]
    try:
        settings = file(FILE_SETTINGS, 'r')
        setts = json.load(settings)
        settings.close()
    except IOError:
        setts = {}
    try:
        sett = {'uname': args[0],
                'passwd': args[1],
                'rq_url': args[2]}
        setts[str(message[u'chat'][u'id'])] = sett
        get_data(sett)
        settings = file(FILE_SETTINGS, 'w')
        json.dump(setts, settings)
        settings.close()
        tg_send(message[u'chat'][u'id'], 'I remember')
    except urllib2.HTTPError:
        tg_send(message[u'chat'][u'id'], 'Your URL is not valid (404?)')
    except urllib2.URLError:
        tg_send(message[u'chat'][u'id'], 'Your URL is not valid (500?)')
    except IndexError:
        tg_msg_hz(message)

def tg_msg_forget(message):
    """Deleting ip, uname, passwd from conf-file"""
    try:
        settings = file(FILE_SETTINGS, 'r')
        setts = json.load(settings)
        settings.close()
    except IOError:
        setts = {}
    del setts[str(message['chat']['id'])]
    settings = file(FILE_SETTINGS, 'w')
    json.dump(setts, settings)
    settings.close()
    tg_send(message['chat']['id'], 'You have been forgotten')

TG_FUNS = {'/reg': tg_msg_reg, '/forget': tg_msg_forget}

def tg_send(chat_id, text):
    """Sending message via Telegram"""
    request = TG_LINK + 'sendMessage?chat_id=' + str(chat_id) + '&text=' + \
              text.encode('utf-8')
    urllib2.urlopen(request)

def get_list(guid, token, sett):
    """Getting list of torrents"""
    request = auth_request(sett['rq_url'] + '?token=' + token + '&list=1', sett)
    request.add_header("Cookie", "GUID=%s;" % guid)
    response = urllib2.urlopen(request)
    return response.read()

def get_data(sett):
    """Getting data(guid, token) from uTorrent by http"""
    request = auth_request(sett['rq_url'] + 'token.html', sett)
    response = urllib2.urlopen(request)
    headers = response.headers.items()
    guid = get_cooka(headers, 'GUID')
    token = get_divka(response.read(), 'token')
    return guid, token

def auth_request(url, data):
    """Authorized request (by CONSTS in a begining of code)"""
    request = urllib2.Request(url)
    base64string = base64.encodestring('%s:%s' %
                                       (data['uname'], data['passwd']))
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
