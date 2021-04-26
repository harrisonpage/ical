# ical.py

Export contents of Apple Calendar to JSON:

* Reads data files directly from ~/Library/Calendar
* Parses URLs and first Zoom URL found
* Events are sorted by date
* Three most recent days are extracted

# Example JSON format

```
{
    "version": "1.2",
    "events": [
        {
            "file": "/Users/harrison/Library/Calendars/DEADBEEF-FFFF-FFFF-FFFF-FFFFFF.caldav/FFFF-FFFF-FFFF-FFFF-DEADBEEF.calendar/Events/example.ics",
            "calendar": "Home",
            "start": 1619812800.0,
            "end": 1619813700.0,
            "summary": "☕ Coffee break",
            "status": "CONFIRMED",
            "desc": "One (1) cup of Silken Splendor please",
            "urls": [],
            "zoom_url": "",
            "attendees": [],
            "busy": "BUSY"
        },
        .
        .
        .
    ]
}
```

Maybe later:

* Migrate hardcoded args to CLI
* Hardcoded to California

Acknowledgements:

* https://stackoverflow.com/a/20941078
* https://github.com/diN0bot/iCal-Analyzer
* https://hasseg.org/icalBuddy/faq.html#Q:+Can+I+get+the+output+in+CSV/(La)TeX/XML/whatever+format?
* https://yanbo.wang/2020/04/22/converting-icalendar-to-csv/

