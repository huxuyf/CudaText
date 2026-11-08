import os
import re
import json
import time
import hashlib
import requests
from urllib.parse import unquote
import cudatext as app
from . import opt
from .work_tempdir import get_temp_dir

_ = lambda s: s

_get_url_busy = False

def get_url(url, fn, del_first=False):
    '''
    Returns True if downloaded OK.
    Returns False if cannot download and Abort pressed.
    Returns None if cannot download and Ignore pressed.
    '''

    global _get_url_busy
    if _get_url_busy:
        print('ERROR: Python downloader is busy, but another plugin called it')
        return
    _get_url_busy = True

    if opt.sf_mirror:
        if url.startswith('https://sourceforge.net/projects/'):
            url += '/download?use_mirror='+opt.sf_mirror

    fn_show = os.path.basename(url)
    fn_temp = fn+'.download'
    if os.path.isfile(fn_temp):
        os.remove(fn_temp)
    if del_first and os.path.isfile(fn):
        os.remove(fn)

    proxies = { 'http': opt.proxy, 'https': opt.proxy, } if opt.proxy else None

    if not opt.verify_https:
        requests.packages.urllib3.disable_warnings()

    while True:
        try:
            r = requests.get(url, proxies=proxies, verify=opt.verify_https, stream=True, timeout=opt.download_timeout)

            size_all = int(r.headers.get('content-length', 0))
            size_got = 0
            percent = 0
            app.app_proc(app.PROC_PROGRESSBAR, 0)
            if fn_show:
                app.msg_status(_('Downloading: ')+(('"'+fn_show+'"') if fn_show else url))
                app.app_proc(app.PROC_IDLE, False)

            with open(fn_temp, 'wb') as f:
                for chunk in r.iter_content(chunk_size=4*1024):
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
                        size_got += len(chunk)
                        if size_all > 0:
                            perc = size_got * 100 // size_all // 4 * 4
                            if perc != percent:
                                percent = perc
                                app.app_proc(app.PROC_PROGRESSBAR, percent)
                                app.app_proc(app.PROC_IDLE, False)

            app.app_proc(app.PROC_PROGRESSBAR, -1)
            app.app_proc(app.PROC_IDLE, False)

            if os.path.isfile(fn_temp):
                if os.path.getsize(fn_temp)==0:
                    raise Exception('Server returned zero-sized file')
                if os.path.isfile(fn):
                    os.remove(fn)
                os.rename(fn_temp, fn)

            _get_url_busy = False
            return True

        except Exception as e:
            res = app.msg_box(_('Cannot download:\n{}\n{}\n\nRetry?').format(url, str(e)),
                app.MB_ABORTRETRYIGNORE + app.MB_ICONWARNING)
            if res != app.ID_RETRY:
                app.app_proc(app.PROC_PROGRESSBAR, -1)
            if res == app.ID_IGNORE:
                _get_url_busy = False
                return
            if res in (app.ID_ABORT, app.ID_CANCEL):
                _get_url_busy = False
                return False


def is_file_html(fn):
    if os.path.exists(fn):
        with open(fn, 'r', encoding='cp437') as f:
            s = f.readline(10).lower()
            return s.startswith('<html>')
    return False


def get_file_sha256(fn):
    '''
    Calculates SHA-256 of a file, returns lowercase hex string.
    '''
    h = hashlib.sha256()
    with open(fn, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def get_plugin_zip(url, sha256=''):
    '''
    Returns .zip filename if downloaded (and verified) ok.
    Returns False if cannot download and Abort pressed, or SHA-256 failed.
    Returns None if cannot download and Ignore pressed.
    '''
    if not url: return
    fn = os.path.join(get_temp_dir(), 'addon.zip')
    res = get_url(url, fn, True)
    if not res:
        return res

    if is_file_html(fn):
        os.remove(fn)

    if os.path.isfile(fn):
        if sha256 and opt.verify_sha256:
            got = get_file_sha256(fn)
            if got.lower() != sha256.lower():
                try:
                    os.remove(fn)
                except Exception:
                    pass
                app.msg_box(_('SHA-256 check failed for downloaded file:\n{}\n\nExpected: {}\nActual: {}\n\nThe file was removed, installation cancelled.').format(url, sha256, got),
                    app.MB_OK + app.MB_ICONERROR)
                return False
        return fn


def file_aged(fn):
    if os.path.isfile(fn):
        age = int(time.time() - os.stat(fn).st_mtime)
        return age > opt.cache_minutes * 60
    else:
        return True


def get_channel(url):
    '''
    Returns list, if channel downloaded OK.
    Returns False, if cannot download and Abort pressed.
    Returns None, if cannot download and Ignore pressed.
    '''
    cap = url.split('/')[-1]

    #separate temp fn for each channel
    temp_dir = os.path.join(get_temp_dir(), 'addon_man')
    if not os.path.isdir(temp_dir):
        os.mkdir(temp_dir)
    temp_fn = os.path.join(temp_dir, cap)

    #download if not cached or cache is aged
    if file_aged(temp_fn):
        print(_('  getting:'), cap)
        res = get_url(url, temp_fn, True)
        if not res: # False or None
            return res
    else:
        print(_('  cached:'), cap)

    if not os.path.isfile(temp_fn):
        return

    text = open(temp_fn, encoding='utf8').read()

    try:
        d = json.loads(text)
    except Exception as e:
        app.msg_box(_('Cannot parse JSON file:\n{}\n{}').format(temp_fn, str(e)),
                app.MB_OK + app.MB_ICONERROR)
        return

    RE = r'http.+/(\w+)\.(.+?)\.zip'
    for item in d:
        if not isinstance(item, dict):
            continue
        url = str(item.get('url', ''))
        parse = re.findall(RE, url)
        item['kind'] = parse[0][0] if parse else ''
        item['name'] = unquote(parse[0][1]) if parse else unquote(os.path.basename(url))
        item['v'] = str(item.get('v', ''))

        #optional metadata; old registry entries don't have these fields
        s = str(item.get('sha256', '')).strip().lower()
        if s.startswith('sha256:'):
            s = s[7:].strip()
        item['sha256'] = s
        item['min_app'] = str(item.get('min_app', '')).strip().lstrip('vV')
        item['max_app'] = str(item.get('max_app', '')).strip().lstrip('vV')
        item['updated'] = str(item.get('updated', '')).strip()

        deps = item.get('deps', [])
        if isinstance(deps, str):
            deps = re.split(r'[,\s]+', deps)
        elif isinstance(deps, (list, tuple)):
            deps = [str(x) for x in deps]
        else:
            deps = []
        item['deps'] = [x.strip() for x in deps if x and x.strip()]

    return d


def get_remote_addons_list(channels):
    res = []
    print(_('Read channels:'))
    for ch in channels:
        items = get_channel(ch)
        if isinstance(items, list):
            res += items
        elif items is None:
            # 'Ignore' pressed
            continue
        else:
            # 'Abort' pressed
            return
    return res
