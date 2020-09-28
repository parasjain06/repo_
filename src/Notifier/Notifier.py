#import pyCiscoSpark
import sys
import requests
import json
import ntpath
#from requests_toolbelt.multipart.encoder import MultipartEncoder
import re

# Helpers
def _url(path):
    return 'https://api.ciscospark.com/v1' + path


def _fix_at(at):
    at_prefix = 'Bearer '
    if not re.match(at_prefix, at):
        return 'Bearer ' + at
    else:
        return at


def get_rooms(at):
    headers = {'Authorization': _fix_at(at)}
    resp = requests.get(_url('/rooms'), headers=headers)
    room_dict = json.loads(resp.text)
    room_dict['statuscode'] = str(resp.status_code)
    return room_dict


def post_message(at, roomId, text, toPersonId='', toPersonEmail=''):
    headers = {'Authorization': _fix_at(at), 'content-type': 'application/json'}
    payload = {'roomId': roomId, 'text': text}
    if toPersonId:
        payload['toPersonId'] = toPersonId
    if toPersonEmail:
        payload['toPersonEmail'] = toPersonEmail
    resp = requests.post(url=_url('/messages'), json=payload, headers=headers)
    message_dict = json.loads(resp.text)
    message_dict['statuscode'] = str(resp.status_code)
    return message_dict

def post_createroom(at, title):
    headers = {'Authorization': _fix_at(at), 'content-type': 'application/json'}
    payload = {'title': title}
    resp = requests.post(url=_url('/rooms'), json=payload, headers=headers)
    create_room_dict = json.loads(resp.text)
    create_room_dict['statuscode'] = str(resp.status_code)
    return create_room_dict


def notify(text):
    print("notified")
    #Initialize parameters
    token = "ZjE2MzcxNzUtYWY2ZC00ZThlLThiMTUtYjYzY2M1OTUxYWEwM2VhYmY2MDktZjk2_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f"
    accesstoken="Bearer "+(token)
    roomname="Wellness"
    room_dict = get_rooms(accesstoken)
    roomid=""
    #Find the roomId
    for room in room_dict['items']:
        if (room['title']==roomname):
            roomid = room['id']

    #Create a room if room does not exist
    if len(roomid) == 0:
        post_createroom(accesstoken,"Wellness")
        # Find the roomId
        for room in room_dict['items']:
            if (room['title'] == roomname):
                roomid = room['id']

    #pyCiscoSpark.post_createroom(accesstoken,"Upright")
    #Send message
    post_message(accesstoken,roomid,text)

