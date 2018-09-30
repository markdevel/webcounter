#!/usr/bin/env python3
""" Traditional Web Counter """

import csv
import os
import re
import uuid
from datetime import datetime, timedelta

import filelock
import pytz
from sanic import Sanic, response


class BaseWebCounter:
    UUID_PATTERN = re.compile(r'^[\dA-Fa-f]{8}-([\dA-Fa-f]{4}-){3}[\dA-Fa-f]{12}$')
    USER_AGENT_PATTERN = re.compile(r'^[\x20-\x7e]{0,255}$')

    def __init__(self):
        self.lock_filename = os.getenv('LOCK_FILENAME', 'css_counter.lock')
        self.count_filename = os.getenv('COUNT_FILENAME', 'count.dat')
        self.log_dirname = os.getenv('LOG_DIRNAME', './log')
        self.timezone = os.getenv('TZ', 'UTC')

    def get_remote_addr(self, request):
        return request.remote_addr or request.ip

    def countup(self, current_time, *args):
        with filelock.FileLock(self.lock_filename):
            fd = os.open(self.count_filename, os.O_RDWR | os.O_CREAT, 0o600)
            count = os.read(fd, 16).decode('utf-8')
            count = int('0' + count) + 1
            os.lseek(fd, 0, os.SEEK_SET)
            os.write(fd, str(count).encode('utf-8'))
            os.close(fd)
            log_filename = os.path.join(self.log_dirname, current_time.strftime("%Y%m") + ".csv")
            with open(log_filename, "a") as log_out:
                writer = csv.writer(log_out, lineterminator='\n')
                writer.writerow((str(count), current_time.isoformat()) + args)
        return count

    def render(self, count):
        raise NotImplementedError

    def output(self, request):
        current_time = datetime.now(tz=pytz.timezone(self.timezone))
        track_id = request.headers.get('If-None-Match') or request.cookies.get('track_id', '')
        if not self.UUID_PATTERN.match(track_id):
            track_id = str(uuid.uuid4())
        count = int('0' + request.cookies.get('previous_count', ''))
        if count <= 0:
            user_agent = request.headers.get('User-Agent', '')
            if not self.USER_AGENT_PATTERN.match(user_agent):
                user_agent = ''
            count = self.countup(current_time, self.get_remote_addr(request), user_agent, track_id)
        res = self.render(count)
        res.headers.add('ETag', track_id)
        res.headers.add('Cache-Control', 'private, must-revalidate, proxy-revalidate')
        res.cookies['previous_count'] = str(count)
        res.cookies['previous_count']['expires'] = current_time + timedelta(minutes=30)
        res.cookies['track_id'] = track_id
        res.cookies['track_id']['expires'] = current_time + timedelta(days=365)
        return res


class JSONCounter(BaseWebCounter):
    def render(self, count):
        return response.json({'count': count})


class HTMLCounter(BaseWebCounter):
    def __init__(self):
        super().__init__()
        self.image_url = os.getenv(
            'IMAGE_URL',
            'data:image/gif;base64,R0lGODlhlgAUAIAAAAAAAP//ACH+JjEwOjA6MTU6MzA6NDU6NjA6NzU'
            '6OTA6MTA1OjEyMDoxMzU6MTUwACwAAAAAlgAUAAAC/4SPqcvtD6OctNqLs978hA+GWEgGSSleKKiu'
            '5unCK2LOL3QbtkwCd674+VCnyc4zLPmQx2GS9YlEedEprWe1wjy13lai1Faxv64oq9WlF6xH2/F+c'
            '8tA9hosXsf16Lqc8WdXF9RHSIdzJ5XnVygzZ4g46OjWeHVIKRlpCanGeLmJqRnayZkkaiEXuOfJBZ'
            'h5ZQgFRIT2NNY6g+ulCBtWZtvVAUdElVKcZoZ1nKioFGus5sob7fx8W+w0R6Z79hrNLWudbTo5/In'
            'K/DhKDtqQyufNrppOWt8SH1g67/3Our5/Kh8efPTkwVvHTp05hQxdnasgsJ27Sg1LJbQ38ZevaTtO'
            'qokrOE7btY7bKPUqaSmcDmBVwDAhtmyJlJhCmsChwbIGzZQeKbiYFeMezE5DfQYVuUuY0qVMmzYoA'
            'AA7')
        self.image_width = int(os.getenv('IMAGE_WIDTH', 150))
        self.image_height = int(os.getenv('IMAGE_HEIGHT', 20))
        self.min_digits = int(os.getenv('MIN_DIGITS', 1))

    def render(self, count):
        n = 10
        sprites = [
            "background:url({0});width:{1}px;height:{2}px;background-position:{3}px 0;display:inline-block".format(
                self.image_url, self.image_width / n, self.image_height, -i * self.image_width / n) for i in range(n)]
        s = "".join(["<div style=\"{0}\"></div>".format(sprites[int(c)]) for c in str(count).zfill(self.min_digits)])
        s = '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, ' \
            'initial-scale=1"></head><body>' + s + '</body></html> '
        return response.html(s)


app = Sanic(__name__)


@app.route('/json')
async def json(request):
    return JSONCounter().output(request)


@app.route('/html')
async def html(request):
    return HTMLCounter().output(request)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
