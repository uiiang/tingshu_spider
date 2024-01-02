
import io
import os
import re
import sys
from urllib import request, parse, error
import log
import socket
import ssl
import logging


force = False
skip_existing_file_size_check = False
auto_rename = False
insecure = False

fake_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',  # noqa
    'Accept-Charset': 'UTF-8,*;q=0.5',
    'Accept-Encoding': 'gzip,deflate,sdch',
    'Accept-Language': 'en-US,en;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.74 Safari/537.36 Edg/79.0.309.43',  # noqa
}


def url_save(
    url, filepath, bar, refer=None, is_part=False, faker=False,
    headers=None, timeout=None, **kwargs
):
    tmp_headers = headers.copy() if headers is not None else {}
    # When a referer specified with param refer,
    # the key must be 'Referer' for the hack here
    if refer is not None:
        tmp_headers['Referer'] = refer
    if type(url) is list:
        chunk_sizes = [url_size(url, faker=faker, headers=tmp_headers) for url in url]
        file_size = sum(chunk_sizes)
        is_chunked, urls = True, url
    else:
        file_size = url_size(url, faker=faker, headers=tmp_headers)
        chunk_sizes = [file_size]
        is_chunked, urls = False, [url]

    continue_renameing = True
    while continue_renameing:
        continue_renameing = False
        if os.path.exists(filepath):
            if not force and (file_size == os.path.getsize(filepath) or skip_existing_file_size_check):
                if not is_part:
                    if bar:
                        bar.done()
                    if skip_existing_file_size_check:
                        log.w(
                            'Skipping {} without checking size: file already exists'.format(
                                os.path.basename(filepath)
                            )
                        )
                    else:
                        log.w(
                            'Skipping {}: file already exists'.format(
                                os.path.basename(filepath)
                            )
                        )
                else:
                    if bar:
                        bar.update_received(file_size)
                return
            else:
                if not is_part:
                    if bar:
                        bar.done()
                    # if not force and auto_rename:
                    #     path, ext = os.path.basename(filepath).rsplit('.', 1)
                    #     finder = re.compile(' \([1-9]\d*?\)$')
                    #     if (finder.search(path) is None):
                    #         thisfile = path + ' (1).' + ext
                    #     else:
                    #         def numreturn(a):
                    #             return ' (' + str(int(a.group()[2:-1]) + 1) + ').'
                    #         thisfile = finder.sub(numreturn, path) + ext
                    #     filepath = os.path.join(os.path.dirname(filepath), thisfile)
                    #     print('Changing name to %s' % os.path.basename(filepath)), '...'
                    #     continue_renameing = True
                    #     continue
                    if log.yes_or_no('File with this name already exists. Overwrite?'):
                        log.w('Overwriting %s ...' % os.path.basename(filepath))
                    else:
                        return
        elif not os.path.exists(os.path.dirname(filepath)):
            os.mkdir(os.path.dirname(filepath))

    temp_filepath = filepath + '.download' if file_size != float('inf') \
        else filepath
    received = 0
    if not force:
        open_mode = 'ab'

        if os.path.exists(temp_filepath):
            received += os.path.getsize(temp_filepath)
            if bar:
                bar.update_received(os.path.getsize(temp_filepath))
    else:
        open_mode = 'wb'

    chunk_start = 0
    chunk_end = 0
    for i, url in enumerate(urls):
        url = parse.quote(url, safe=";/?:@&=+$,",encoding='utf-8')
        received_chunk = 0
        chunk_start += 0 if i == 0 else chunk_sizes[i - 1]
        chunk_end += chunk_sizes[i]
        if received < file_size and received < chunk_end:
            if faker:
                tmp_headers = fake_headers
            '''
            if parameter headers passed in, we have it copied as tmp_header
            elif headers:
                headers = headers
            else:
                headers = {}
            '''
            if received:
                # chunk_start will always be 0 if not chunked
                tmp_headers['Range'] = 'bytes=' + str(received - chunk_start) + '-'
            if refer:
                tmp_headers['Referer'] = refer
            log.w()
            log.w(f'开始下载{os.path.basename(filepath)}')
            if timeout:
                response = urlopen_with_retry(
                    request.Request(url, headers=tmp_headers), timeout=timeout
                )
            else:
                response = urlopen_with_retry(
                    request.Request(url, headers=tmp_headers)
                )
            try:
                range_start = int(
                    response.headers[
                        'content-range'
                    ][6:].split('/')[0].split('-')[0]
                )
                end_length = int(
                    response.headers['content-range'][6:].split('/')[1]
                )
                range_length = end_length - range_start
            except:
                content_length = response.headers['content-length']
                range_length = int(content_length) if content_length is not None \
                    else float('inf')

            if is_chunked:  # always append if chunked
                open_mode = 'ab'
            elif file_size != received + range_length:  # is it ever necessary?
                received = 0
                if bar:
                    bar.received = 0
                open_mode = 'wb'

            with open(temp_filepath, open_mode) as output:
                while True:
                    buffer = None
                    try:
                        buffer = response.read(1024 * 256)
                    except socket.timeout:
                        pass
                    if not buffer:
                        if is_chunked and received_chunk == range_length:
                            break
                        elif not is_chunked and received == file_size:  # Download finished
                            break
                        # Unexpected termination. Retry request
                        tmp_headers['Range'] = 'bytes=' + str(received - chunk_start) + '-'
                        response = urlopen_with_retry(
                            request.Request(url, headers=tmp_headers)
                        )
                        continue
                    output.write(buffer)
                    received += len(buffer)
                    received_chunk += len(buffer)
                    if bar:
                        bar.update_received(len(buffer))

    assert received == os.path.getsize(temp_filepath), '%s == %s == %s' % (
        received, os.path.getsize(temp_filepath), temp_filepath
    )

    if os.access(filepath, os.W_OK):
        # on Windows rename could fail if destination filepath exists
        os.remove(filepath)
    os.rename(temp_filepath, filepath)


def urlopen_with_retry(*args, **kwargs):
    retry_time = 3
    for i in range(retry_time):
        try:
            if insecure:
                # ignore ssl errors
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                return request.urlopen(*args, context=ctx, **kwargs)
            else:
                return request.urlopen(*args, **kwargs)
        except socket.timeout as e:
            logging.debug('request attempt %s timeout' % str(i + 1))
            if i + 1 == retry_time:
                raise e
        # try to tackle youku CDN fails
        except error.HTTPError as http_error:
            logging.debug('HTTP Error with code{}'.format(http_error.code))
            if i + 1 == retry_time:
                raise http_error


def url_size(url, faker=False, headers={}):
    url = parse.quote(url, safe=";/?:@&=+$,",encoding='utf-8')
    if faker:
        response = urlopen_with_retry(
            request.Request(url, headers=fake_headers)
        )
    elif headers:
        response = urlopen_with_retry(request.Request(url, headers=headers))
    else:
        response = urlopen_with_retry(url)

    size = response.headers['content-length']
    return int(size) if size is not None else float('inf')


def urls_size(urls, faker=False, headers={}):
    return sum([url_size(url, faker=faker, headers=headers) for url in urls])


class PiecesProgressBar:
    def __init__(self, total_size, total_pieces=1):
        self.displayed = False
        self.total_size = total_size
        self.total_pieces = total_pieces
        self.current_piece = 1
        self.received = 0

    def update(self):
        self.displayed = True
        bar = '{0:>5}%[{1:<40}] {2}/{3}'.format(
            '', '=' * 40, self.current_piece, self.total_pieces
        )
        sys.stdout.write('\r' + bar)
        sys.stdout.flush()

    def update_received(self, n):
        self.received += n
        self.update()

    def update_piece(self, n):
        self.current_piece = n

    def done(self):
        if self.displayed:
            print()
            self.displayed = False



# if __name__ == "__main__":
#     title = 'test download'
#     if not os.path.exists(title):
#         print(f'创建文件夹{title}')
#         os.makedirs(title)
#     url='http://117.65.18.37:50010/myfiles/host/listen/听书目录/清明上河图密码~冶文彪~读客熊猫君/ef9a3acb94ff455da461767185f24fef.m4a'
#     bar = PiecesProgressBar(1,1)
#     bar.update()
#     # print(f'url == {parse.quote(url, safe=";/?:@&=+$,",encoding="utf-8")}')
#     url_save(url=url,
#         filepath=os.path.join(title, '103_主动投案.m4a'),
#         bar=bar, refer=None, merge=True,
#         faker=False, headers=fake_headers)
#     bar.done()
#     pass