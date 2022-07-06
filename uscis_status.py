from random import randint
import requests
import time
import json
from pyquery import PyQuery as pq
from os import path, getenv
import sys
from dotenv import load_dotenv
import arrow
from pushover import init, Client
from datetime import datetime
from datetime import time as dt_time

STATUS_OK = 0
STATUS_ERROR = -1
FILENAME_LASTSTATUS = path.join(sys.path[0], "LAST_STATUS_{0}.txt")

load_dotenv()

casenumber = "IOE8431147431"
day_delay = 3600 # 1 hour
night_delay = 32400 # 9 hrs
pushover_user_key = "u1rt7p5ubvobb9fai6ddt4s3cdyifi"
pushover_app_key = "agqy9embj6y35gwwv6hrcjxkejy7s4"

casenumber = getenv('CASE_NUMBER')
day_delay = int(getenv('DELAY_MIN'))
night_delay = int(getenv('DELAY_MAX'))
pushover_user_key = getenv('PUSHOVER_USER_KEY')
pushover_app_key = getenv('PUSHOVER_APP_KEY')

notify = Client(pushover_user_key, api_token=pushover_app_key)

def poll_status(casenumber):
    headers = {
        'Accept': 'text/html, application/xhtml+xml, image/jxr, */*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language':
        'en-US, en; q=0.8, zh-Hans-CN; q=0.5, zh-Hans; q=0.3',
        'Cache-Control': 'no-cache',
        'Connection': 'Keep-Alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'egov.uscis.gov',
        'Referer': 'https://egov.uscis.gov/casestatus/mycasestatus.do',
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' +
        'AppleWebKit/537.36 (KHTML, like Gecko) ' +
        'Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586'
    }
    url = "https://egov.uscis.gov/casestatus/mycasestatus.do"
    data = {"appReceiptNum": casenumber, 'caseStatusSearchBtn': 'CHECK+STATUS'}

    res = requests.post(url, data=data, headers=headers)
    doc = pq(res.text)
    status = doc('h1').text()
    code = STATUS_OK if status else STATUS_ERROR
    details = doc('.text-center p').text()
    return (code, status, details)


def on_status_fetch(status, casenumber):
    status = status.strip()
    record_filepath = FILENAME_LASTSTATUS.format(casenumber)
    changed = False
    last_status = None
    if not path.exists(record_filepath):
        with open(record_filepath, 'w') as f:
            f.write(status)
    else:
        with open(record_filepath, 'r+') as f:
            last_status = f.read().strip()
            if status != last_status:
                changed = True
                f.seek(0)
                f.truncate()
                f.write(status)
    return (changed, status)

def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current UTC time
    check_time = check_time or datetime.utcnow().time()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else: # crosses midnight
        return check_time >= begin_time or check_time <= end_time

def main():
    print(arrow.utcnow().to('US/Pacific').format("MMM D, YYYY h:mm:ssA"))
    print('Starting Script')
    try:
        while True:
            code, status, detail = poll_status(casenumber)
            print(
                arrow.utcnow()
                .to('US/Pacific')
                .format("MMM D, YYYY h:mm:ssA"))
            if code == STATUS_ERROR:
                notify.send_message('Invalid Case Number. Sleeping for {%s/60} Minutes' % (delay))
                print('Invalid Case Number. Sleeping for {%s/60} Minutes' % (delay))
                time.sleep(delay)
                continue

            changed, status = on_status_fetch(status, casenumber)

            print(status)
            if changed:
                notify.send_message('Status Updated: %s' % (status))
            else:
                notify.send_message('No change in status: %s' % (status))
            
            delay = day_delay
            if is_time_between(dt_time(14,00), dt_time(5,00)):
                delay = day_delay
            else:
                delay = night_delay

            delay_mins = int(delay/60)
            print('Sleeping for %s Minutes' % (delay_mins))
            time.sleep(delay)

    except Exception as e:
        print(e)
        notify.send_message('Script error')
        pass

    print('Ending Script')
    notify.send_message('Script end')


if __name__ == "__main__":
    main()
