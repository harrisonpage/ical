#!/usr/bin/env python3

import datetime
from icalendar import Calendar
import json
import os
from pathlib import Path
import plistlib
import pytz
import re
import sys
import time

VERSION = 1.2
FUTURE_DAYS = 3
CALENDAR_DIR = os.path.join(str(Path.home()), 'Library', 'Calendars')
URL_REGEX = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:\'\".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""
PST = pytz.timezone('US/Pacific')

def parse_ics(file, events, calendar, now, cutoff):
    with open(file, 'r', encoding='utf-8') as ical_event:
        data = ical_event.read()

    cal = Calendar.from_ical(data)

    for event in cal.subcomponents:
        # skip unwanted events
        if event.name != 'VEVENT':
            continue

        # all-day events expressed as datetime.date, convert these to datetime.datetime
        try:
            start = event.get('DTSTART').dt.astimezone(PST).timestamp()
        except (AttributeError):
            start = datetime.datetime.combine(event.get('DTSTART').dt, datetime.datetime.min.time()).astimezone(PST).timestamp()

        # ignore events that are too old or too far in the future
        if start < now or start > cutoff:
            continue

        desc = str(event.get('DESCRIPTION'))

        # extract URLs and find the first zoom.us URL
        urls = re.findall(URL_REGEX, desc)
        zoom_url = urls[0] if len(urls) and 'zoom.us' in urls[0] else ''

        # extract attendees. when there's only 1 it comes back as a string, migrate into list form
        attendee_raw = event.get('ATTENDEE')
        attendees = []
        if attendee_raw is not None and len(attendee_raw):
            if isinstance(attendee_raw, list):
                for a in attendee_raw:
                    attendees.append(str(a).replace('mailto:', ''))
            else:
                attendees.append(str(attendee_raw).replace('mailto:', ''))

        try:
            end = event.get('DTEND').dt.astimezone(PST).timestamp()
        except (AttributeError):
            end = datetime.datetime.combine(event.get('DTEND').dt, datetime.datetime.min.time()).astimezone(PST).timestamp()

        summary = str(event.get('SUMMARY'))
        events.append({
            'file': file,
            'calendar': calendar,
            'start': start,
            'end': end,
            'summary': summary,
            'status': str(event.get('STATUS')),
            'desc': desc,
            'urls': urls,
            'zoom_url': zoom_url,
            'attendees': attendees,
            'busy': str(event.get('X-APPLE-EWS-BUSYSTATUS')),
        })

# extract a calendar's title
def parse_calendar(file):
    with open(file, 'rb') as f:
        info = plistlib.load(f)
    return info['Title']

def main():
    events = []
    calendar = None

    # today's date
    now = (datetime.datetime.now() - datetime.timedelta(hours=8)).timestamp()

    # future date
    cutoff = (datetime.datetime.now() + datetime.timedelta(days=FUTURE_DAYS)).timestamp()

    # walk through ~/Library/Calendar looking for .ics and .calendar files
    for root, dirs, files in os.walk(CALENDAR_DIR, topdown=True):
        for name in files:
            file = os.path.join(root, name)
            if os.path.isfile(file):
                if name.endswith('.ics'):
                    parse_ics(file, events, calendar, now, cutoff)
                elif root.endswith('.calendar') and name.endswith('Info.plist'):
                    calendar = parse_calendar(file)

    # sort events by date
    events.sort(key=lambda x:x['start'])

    print(json.dumps({
            'events': events,
            'version': VERSION},
        indent=4, default=str))

if __name__ == '__main__': main()
