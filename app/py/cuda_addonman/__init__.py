import os
import re
import shutil
import json
import collections
import subprocess
from cudatext import *
from urllib.parse import unquote
from .work_local import *
from .work_remote import *
from .work_dlg_config import *
from .work_github import *
from .work_install_helper import after_install
from .work_cudatext_updates__sourceforge import check_cudatext
from . import opt

from cudax_lib import get_translation, safe_open_url
_   = get_translation(__file__)  # i18n

_homedir = os.path.expanduser('~')
dir_for_all = os.path.join(_homedir, 'CudaText_addons')
fn_config = os.path.join(app_path(APP_DIR_SETTINGS), 'cuda_addonman.json')

def collapse_filename(fn):
    if (fn+'/').startswith(_homedir+'/'):
        fn = fn.replace(_homedir, '~', 1)
    return fn

CATEGORY = _('Category')
PREINST = 'preinstalled'
STD_MODULES = (
  'cuda_addonman',
  'cuda_comments',
  'cuda_insert_time',
  'cuda_make_plugin',
  'cuda_multi_installer',
  'cuda_new_file',
  'cuda_prefs',
  'cuda_palette',
  'cuda_project_man',
  'cuda_snippet_panel',
  'cuda_sort',
  'cuda_tabs_list',
  'cuda_lexer_detecter',
  )
STD_LEXERS = (
  'Bash script',
  'Batch files',
  'CSS',
  'Diff',
  'HTML',
  'HTML style',
  'JavaScript',
  'JSDoc',
  'JSON',
  'Markdown',
  'Python',
  'RegEx',
  'reStructuredText',
  'Search results',
  'XML',
  'YAML',
)
STD_LEXERS_LITE = (
  'Ini files',
  'JSON',
  'Log files',
  'SQL',
  'XML',
  'Config-RC',
)
STD_THEMES = (
  'amy',
  'cobalt',
  'darkwolf',
  'ebony',
  'green',
  'navy',
  'sub',
  'syn',
)
STD_TOOLBARICONS = (
  'default_24x24',
  'light_24x24',
)
STD_SIDEBARICONS = (
  'common_20x20',
  'octicons_20x20',
)
STD_CODETREEICONS = (
  'default_16x16',
)
STD_TRANSLATIONS = (
  'translation template',
)
STD_SNIPPETS = (
  'Std.HtmlTags',
  'Std.Php',
)


def get_app_compat(info):
    '''
    Checks CudaText version range of a registry item.
    Returns (ok, reason). Missing fields mean no restriction.
    '''
    app_ver = app_exe_version()
    s_min = str(info.get('min_app', '')).strip()
    s_max = str(info.get('max_app', '')).strip()
    if s_min and compare_versions(app_ver, s_min) < 0:
        return False, _('requires CudaText {} or newer (current {})').format(s_min, app_ver)
    if s_max and compare_versions(app_ver, s_max) > 0:
        return False, _('supports CudaText up to {} (current {})').format(s_max, app_ver)
    return True, ''


def find_registry_item(items, dep):
    '''
    Finds a registry item by 'kind.name', module name, or zip file name.
    '''
    dep = (dep or '').strip()
    if not dep:
        return None
    dep_zip = dep if dep.endswith('.zip') else dep+'.zip'
    for i in items:
        base = os.path.basename(i.get('url', ''))
        if base == dep_zip:
            return i
        if i.get('module', '') == dep:
            return i
        if (i.get('kind', '')+'.'+i.get('name', '')) == dep:
            return i
    return None


def show_addon_details(info):
    '''
    Shows metadata of a registry item in a message box.
    '''
    lines = []
    lines.append(_('Kind:') + ' ' + info.get('kind', ''))
    lines.append(_('Name:') + ' ' + info.get('name', ''))
    if info.get('module'):
        lines.append(_('Module:') + ' ' + info['module'])
    lines.append(_('Local version:') + ' ' + str(info.get('v_local', '?') or '?'))
    lines.append(_('Web version:') + ' ' + str(info.get('v', '') or '?'))
    lines.append(_('Updated:') + ' ' + str(info.get('updated', '') or info.get('v', '') or '?'))

    s = _('App version range:') + ' '
    if info.get('min_app') or info.get('max_app'):
        s += '{}..{}'.format(info.get('min_app') or '*', info.get('max_app') or '*')
    else:
        s += '*..*'
    ok, reason = get_app_compat(info)
    if not ok:
        s += ' (' + reason + ')'
    lines.append(s)

    lines.append(_('SHA-256:') + ' ' + (_('present') if info.get('sha256') else _('not provided')))
    lines.append(_('Dependencies:') + ' ' + (', '.join(info.get('deps', [])) or _('none')))
    if info.get('req'):
        lines.append(_('Requirements:') + ' ' + str(info['req']))
    lines.append(_('URL:') + ' ' + str(info.get('url', '')))

    msg_box('\n'.join(lines), MB_OK+MB_ICONINFO)


class Command:

    def __init__(self):
        if os.path.isfile(fn_config):
            data = json.loads(open(fn_config).read(), object_pairs_hook=collections.OrderedDict)
            opt.ch_user = data.get('channels_user', opt.ch_user)
            opt.suggest_readme = data.get('suggest_readme', True)
            opt.install_confirm = data.get('install_confirm', True)
            opt.verify_https = data.get('verify_https', True)
            opt.verify_sha256 = data.get('verify_sha256', True)
            opt.proxy = data.get('proxy', '')
            opt.sf_mirror = data.get('sf_mirror', '')


    def do_config(self):
        res = do_config_dialog()
        if res is None: return

        data = {}
        data['channels_user'] = opt.ch_user
        data['suggest_readme'] = opt.suggest_readme
        data['install_confirm'] = opt.install_confirm
        data['verify_https'] = opt.verify_https
        data['verify_sha256'] = opt.verify_sha256
        data['proxy'] = opt.proxy
        data['sf_mirror'] = opt.sf_mirror

        with open(fn_config, 'w') as f:
            f.write(json.dumps(data, indent=4))


    def do_show_links(self):

        # msg_status(_('Downloading list...'))
        items = get_remote_addons_list(opt.ch_def+opt.ch_user)
        msg_status('')
        if not items:
            msg_status(_('Cannot download list'))
            return

        res = sorted([item['url'] for item in items])
        file_open('')
        ed.set_text_all('\n'.join(res)+'\n')


    def do_download_all(self):
        global dir_for_all
        res = dlg_input(_('Folder to save files:'), dir_for_all)
        if not res: return
        dir_for_all = res
        if not os.path.isdir(dir_for_all):
            os.mkdir(dir_for_all)
        if not os.path.isdir(dir_for_all):
            msg_box(_('Cannot create dir: ')+dir_for_all, MB_OK+MB_ICONERROR)
            return

        # msg_status(_('Downloading list...'))
        items = get_remote_addons_list(opt.ch_def+opt.ch_user)
        msg_status('')
        if not items:
            msg_status(_('Cannot download list'))
            return

        self.init_progress()
        self.stopped = False
        self.stopped_force = False
        self.stopped_msg = ''
        dlg_proc(self.h_pro, DLG_SHOW_NONMODAL)

        err = 0

        for (i, item) in enumerate(items):
            url = item['url']

            if self.stopped:
                self.stopped_force = True
                self.stopped_msg = _('(got {} of {} files)').format(i+1, len(items))
                break

            percent = (i+1)*100//len(items)
            text = _('Downloading: {}/{}').format(i+1, len(items))
            self.show_progress(percent, text)

            name = unquote(url.split('/')[-1])
            dir = os.path.join(dir_for_all, name.split('.')[0])
            if not os.path.isdir(dir):
                os.mkdir(dir)
            fn = os.path.join(dir, name)
            res = get_url(url, fn)
            if res is False: #abort button
                break
            if not os.path.isfile(fn):
                err += 1
                print(_('Cannot download file: ')+url)
                continue

        self.hide_progress()

        text = _('Download complete') if not self.stopped_force else _('Download stopped ')+self.stopped_msg
        if err>0:
            text += _('\nErrors occurred, see Python console')
        msg_box(text, MB_OK+MB_ICONINFO)


    def get_item_label(self, item, installed_modules, installed_lexers):

        def is_item_installed(item):

            if item['kind']=='lexer':
                return item['name'] in installed_lexers
            else:
                return item.get('module', '') in installed_modules

        if not is_item_installed(item):
            return ''

        if item['kind']=='plugin':
            if os.path.isdir(DIR_PY+'/'+item['module']+'/.git'):
                return ' ◄git►'

        v_remote = item.get('v', '')
        v_local = work_local.get_addon_version(item.get('url', ''))
        if not v_remote or compare_versions(v_local, v_remote)>=0:
            res = ' ◄local {}►'.format(v_local or '?')
        else:
            res = ' ▲local {}, web {} ◄'.format(v_local or '?', v_remote)
        return res


    def do_install_addon(self):

        caption = _('Install')
        # msg_status(_('Downloading list...'))
        items = get_remote_addons_list(opt.ch_def+opt.ch_user)
        msg_status('')
        if not items:
            msg_status(_('Cannot download list'))
            return

        items = sorted(items,
            key=lambda item: (item['kind'], item['name'])
            )

        kinds = sorted(list(set([i['kind'] for i in items])))

        installed = get_installed_addons()
        installed_modules = [i['module'] for i in installed if i['kind']=='plugin']
        installed_lexers = [i['name'].replace(' ', '_') for i in installed if i['kind']=='lexer']

        names = ['<'+CATEGORY+'>'] + \
            [ i['kind'] + ': ' + i['name'] + \
            self.get_item_label(i, installed_modules, installed_lexers) + \
            '\t' + i['desc'] for i in items ]

        res = dlg_menu(
            DMENU_LIST_ALT+DMENU_NO_FULLFILTER,
            names,
            caption=caption
            )
        if res is None: return

        if res==0:
            #chosen item 'Category', show menu again
            res = dlg_menu(
                DMENU_LIST,
                kinds,
                caption=CATEGORY
                )
            if res is None: return

            need_kind = kinds[res]
            items = [ i for i in items if i['kind']==need_kind ]
            names = [ i['kind'] + ': ' + i['name'] + \
                self.get_item_label(i, installed_modules, installed_lexers) + \
                '\t' + i['desc'] for i in items ]

            res = dlg_menu(
                DMENU_LIST_ALT+DMENU_NO_FULLFILTER,
                names,
                caption=caption+' / '+CATEGORY+' "'+need_kind+'"'
                )
            if res is None: return
        else:
            #for choice not from 'category', skip 1 first item 'Category'
            res -= 1

        info = items[res]
        #print('Chosen addon:', info)
        name = info['name']
        req = info.get('req', '')
        req_names = req.split(',') if req else []

        if info['kind']=='linter':
            if not 'cuda_lint' in installed_modules:
                req_names.append('plugin.CudaLint')

        if info['kind']=='formatter':
            if not 'cuda_fmt' in installed_modules:
                req_names.append('plugin.CudaFormatter')

        #new optional metadata: dependencies
        for s in info.get('deps', []):
            req_names.append(s)

        req_items = []
        for s in req_names:
            item_dep = find_registry_item(items, s)
            if item_dep and not item_dep in req_items:
                req_items.append(item_dep)

        if req_items:
            nice_names = '* '+'\n* '.join([i['kind']+' '+i['name'] for i in req_items])
            if msg_box(_('Add-on "{}" requires:\n\n{}\n\nRequirements will be auto-installed. Proceed?').format(name, nice_names),
                MB_OKCANCEL+MB_ICONQUESTION)!=ID_OK:
                return

            for item in req_items:
                if not self.do_install_single(item, True, False):
                    return

        self.do_install_single(info,
            not opt.install_confirm,
            opt.suggest_readme)


    def do_install_single(self, info, is_silent, suggest_readme):
        '''
        Returns True if downloaded and installed.
        Returns None if cannot download nor install.
        '''

        name = info['name']
        url = info['url']
        version = info['v']
        kind = info['kind']

        ok_compat, reason = get_app_compat(info)
        if not ok_compat:
            msg_box(_('Cannot install add-on "{}":\n\n{}\n\nPlease update CudaText or skip this add-on.').format(name, reason),
                MB_OK+MB_ICONWARNING)
            msg_status(_('Installation cancelled'))
            return

        #download
        fn = get_plugin_zip(url, info.get('sha256', ''))
        if fn is None or fn==False or not os.path.isfile(fn):
            msg_status(_('Cannot download file'))
            return

        s_options = '/silent' if is_silent else ''
        ok = file_open(fn, options=s_options)

        msg_status(_('Addon installed') if ok else _('Installation cancelled'))
        if not ok:
            os.remove(fn)
            return

        #save version
        props = do_save_version(url, fn, version)
        os.remove(fn)

        if props:
            #suggest readme
            m = props[2]
            if m:
                after_install(m)

            if m and suggest_readme:
                names = []
                fn = get_readme_of_module(m)
                if fn:
                    names.append((get_name_of_module(m)+_(': view readme'), fn))
                fn = get_history_of_module(m)
                if fn:
                    names.append((get_name_of_module(m)+_(': view history'), fn))

                if names:
                    res = dlg_menu(DMENU_LIST, [s[0] for s in names], caption=_('Readme'))
                    if res is None: return
                    file_open(names[res][1])

        return True


    def do_install_lexer(self):
        """Not used. For future? Suggest only lexers to install"""

        items = get_avail_list()
        items = [l for l in items if l[0].startswith('Lexer:')]

        res = dlg_menu(DMENU_LIST, [l[0] for l in items])
        if res is None: return
        res = items[res]
        url = get_item_url(res[2])
        fn = get_plugin_zip(url)
        if os.path.isfile(fn):
            file_open(fn)

    def do_remove(self):

        ignored = {
            'plugins': STD_MODULES,
            'lexers': STD_LEXERS,
            'lexers_lite': STD_LEXERS_LITE,
            'themes': STD_THEMES,
            'toolbaricons': STD_TOOLBARICONS,
            'sidebaricons': STD_SIDEBARICONS,
            'codetreeicons': STD_CODETREEICONS,
            'lang': STD_TRANSLATIONS,
            'snippets': STD_SNIPPETS,
            }
        items = get_installed_addons(ignored)
        desc = [i['kind']+': '+i['name'] for i in items]

        res = dlg_menu(DMENU_LIST, desc, caption=_('Remove add-on'))
        if res is None: return

        item = items[res]
        if msg_box(_('Remove {}: {}').format(item['kind'], item['name']), MB_OKCANCEL+MB_ICONQUESTION)!=ID_OK:
            return

        module = item.get('module', '')
        if module:
            do_remove_version_of_plugin(module)
        elif item['kind'] == 'lexer':
            do_remove_version_of_lexer(item['name'])

        ok = True
        for fn in item['files']:
            if fn.endswith('/'):
                fn = fn[:-1]
                ok = do_remove_dir(fn)
            else:
                if os.path.isfile(fn):
                    os.remove(fn)
        if ok:
            msg_box(_('Removed, restart program to see changes'), MB_OK+MB_ICONINFO)


    def do_edit(self):
        m = get_installed_choice(_('Edit'))
        if m is None: return
        fn = get_initpy_of_module(m)
        file_open(fn)
        msg_status(_('Opened: ')+collapse_filename(fn))

    def do_homepage(self):
        m = get_installed_choice(_('Visit homepage'))
        if m is None: return
        s = get_homepage_of_module(m)
        if s:
            safe_open_url(s)
            msg_status(_('Opened browser: ')+s)
        else:
            msg_box(_('Plugin "%s" doesn\'t have "homepage" field in install.inf') % \
              get_name_of_module(m), MB_OK+MB_ICONWARNING)

    def do_readme(self):
        m = get_installed_choice(_('Open readme'))
        if m is None: return
        s = get_readme_of_module(m)
        if s:
            file_open(s)
        else:
            msg_status(_('Plugin "%s" doesn\'t have readme') % get_name_of_module(m))

    def do_history(self):
        m = get_installed_choice(_('Open history'))
        if m is None: return
        s = get_history_of_module(m)
        if s:
            file_open(s)
        else:
            msg_status(_('Plugin "%s" doesn\'t have history') % get_name_of_module(m))


    def do_update(self):

        def fix_name(s, del_brackets):
            s = s.replace(' ', '_')
            # strip additions in name for "gruvbox (Dark) (Medium)"
            if del_brackets:
                n = s.find('_(')
                if n>=0:
                    s = s[:n]
            return s

        dir_py = DIR_PY

        # msg_status(_('Downloading list...'))
        addons = get_remote_addons_list(opt.ch_def+opt.ch_user)
        msg_status('')
        if not addons:
            msg_status(_('Cannot download list'))
            return

        modules = get_installed_modules()
        modules_git = [m for m in modules if os.path.isdir(os.path.join(dir_py, m, '.git'))]
        modules = [m for m in modules if not m in modules_git]

        installed = get_installed_addons()
        lexers = [fix_name(i['name'], False) for i in installed if i['kind']=='lexer']
        langs = [fix_name(i['name'], False) for i in installed if i['kind']=='translation']
        themes = [fix_name(i['name'], True) for i in installed if i['kind']=='theme']

        addons = [a for a in addons if a['kind'] in ('plugin', 'treehelper', 'linter', 'formatter') and a.get('module', '') in modules] \
               + [a for a in addons if a['kind']=='lexer' and a['name'] in lexers] \
               + [a for a in addons if a['kind']=='translation' and a['name'] in langs] \
               + [a for a in addons if a['kind']=='theme' and a['name'].lower() in themes]

        modules_web = [a.get('module', '') for a in addons]
        modules_web = [a for a in modules_web if a]
        modules_local = [m for m in modules if m not in modules_web]

        for a in addons:
            m = a.get('module', '')

            if a['kind']=='lexer':
                a['dir'] = 'data/lexlib'
            elif a['kind']=='translation':
                a['dir'] = 'data/lang'
            elif a['kind']=='theme':
                a['dir'] = 'data/themes'
            else:
                a['dir'] = 'py/'+m

            v_local = '?'
            if m in STD_MODULES:
                v_local = PREINST
            url = a['url']
            v_remote = a['v']

            v_local = get_addon_version(url) or v_local
            a['v_local'] = v_local

            a['outdated'] = (v_local!=PREINST) and bool(v_remote) and compare_versions(v_local, v_remote)<0
            ok_compat, reason = get_app_compat(a)
            a['compat'] = ok_compat
            a['compat_reason'] = reason
            a['check'] = a['outdated'] and ok_compat

        for m in modules_git:
            d = {}
            d['module'] = m
            d['dir'] = 'py/'+m
            d['kind'] = 'plugin'
            d['name'] = get_name_of_module(m)
            d['v_local'] = 'Git'
            d['v'] = 'Git'
            d['url'] = ''
            d['check'] = False
            d['outdated'] = False
            d['compat'] = True
            d['compat_reason'] = ''
            d['sha256'] = ''
            d['deps'] = []
            d['updated'] = ''
            addons.append(d)

        KIND_ORDER = {
            'plugin': 1,
            'linter': 2,
            'formatter': 3,
            'treehelper': 4,
            'snippets_ct': 50,
            'theme': 100,
            'toolbartheme': 101,
            'toolbarxicons': 102,
            'sidebartheme': 103,
            'projtoolbaricons': 104,
            'filetypeicons': 105,
            'codetreeicons': 106,
            'translation': 200,
            'plugintranslation': 201,
            'buildsystem': 300,
            'lexer': 500,
            'package': 600,
        }

        # show plugins first, ..., lexers last
        addons = sorted(addons, key=lambda i: (
            KIND_ORDER.get(i['kind'], 301),
            i['name'],
            i.get('module', ''),
            ))

        def name_cell(i):
            if i.get('check'):
                prefix = '▲ '
            elif i.get('outdated'):
                prefix = '! '
            else:
                prefix = '  '
            return prefix+'['+i['kind']+'] '+i['name']

        def date_cell(i):
            return i.get('updated', '') or i.get('v', '')

        text_headers = '\r'.join((_('Name=245'), _('Folder=150'), _('Local=105'), _('Available=105'), _('Date=95')))
        text_columns = ['\r'.join((name_cell(i), i['dir'], i['v_local'], i['v'], date_cell(i))) for i in addons]
        text_items = '\t'.join([text_headers]+text_columns)
        text_checks = ['1' if i['check'] else '0' for i in addons]
        text_val = '0;'+','.join(text_checks)
        text_val_initial = text_val

        n_upd = len([i for i in addons if i.get('check')])
        n_bad = len([i for i in addons if i.get('outdated') and not i.get('compat')])
        s_sum = _('Upgradable add-ons: {}').format(n_upd)
        if n_bad:
            s_sum += _('; incompatible: {}').format(n_bad)
        if not n_upd:
            s_sum += ' - '+_('nothing to update')

        RES_OK = 0
        RES_CANCEL = 1
        RES_LIST = 2
        RES_SEL_NONE = 3
        RES_SEL_NEW = 4
        RES_DETAILS = 5
        RES_ALL = 6
        c1 = chr(1)
        DLG_W = 750
        DLG_H = 600
        addons_selected = []

        while True:
            text = '\n'.join([
              c1.join(['type=button', 'pos=%d,%d,%d,%d'%(DLG_W-212, DLG_H-32, DLG_W-112, 0), 'cap='+_('Update'), 'ex0=1']),
              c1.join(['type=button', 'pos=%d,%d,%d,%d'%(DLG_W-106, DLG_H-32, DLG_W-6, 0), 'cap='+_('Cancel')]),
              c1.join(['type=checklistview', 'pos=%d,%d,%d,%d'%(6, 6, DLG_W-6, DLG_H-64), 'items='+text_items, 'val='+text_val, 'ex0=1']),
              c1.join(['type=button', 'pos=%d,%d,%d,%d'%(6, DLG_H-32, 100, 0), 'cap='+_('Deselect all')]),
              c1.join(['type=button', 'pos=%d,%d,%d,%d'%(106, DLG_H-32, 200, 0), 'cap='+_('Select new')]),
              c1.join(['type=button', 'pos=%d,%d,%d,%d'%(206, DLG_H-32, 300, 0), 'cap='+_('Details')]),
              c1.join(['type=button', 'pos=%d,%d,%d,%d'%(306, DLG_H-32, 420, 0), 'cap='+_('Upgrade all')]),
              c1.join(['type=label', 'pos=%d,%d,%d,%d'%(6, DLG_H-58, DLG_W-6, 0), 'cap='+s_sum]),
              ])

            res = dlg_custom(_('Update add-ons'), DLG_W, DLG_H, text)
            if res is None: return

            res, text = res
            if res == RES_SEL_NONE:
                text_val = '0;'
                continue
            if res == RES_SEL_NEW:
                text_val = text_val_initial
                continue
            if res == RES_DETAILS:
                # keep current checks, show details for the focused row
                lines = text.splitlines()
                if len(lines) > RES_LIST:
                    parts = lines[RES_LIST].split(';')
                    sel = parts[0] if parts else '0'
                    checks = parts[1] if len(parts)>1 else ''
                    text_val = sel+';'+checks
                    try:
                        idx = int(sel)
                    except Exception:
                        idx = -1
                    if 0<=idx<len(addons):
                        show_addon_details(addons[idx])
                continue
            if res == RES_CANCEL:
                return
            if res == RES_ALL:
                addons_selected = [i for i in addons if i.get('check')]
                break
            if res == RES_OK:
                lines = text.splitlines()[RES_LIST]
                states = lines.split(';')[1].split(',')
                addons_selected = [a for (i, a) in enumerate(addons) if i<len(states) and states[i]=='1']
                break

        if not addons_selected:
            return

        self.init_progress(_('Updating add-ons'))
        self.stopped = False
        self.stopped_force = False
        self.stopped_msg = ''
        dlg_proc(self.h_pro, DLG_SHOW_NONMODAL)

        ok_count = 0
        skip_count = 0
        fail_count = 0
        skipped = []
        failed = []
        print(_('Updating addons:'))

        try:
            for (a_index, a) in enumerate(addons_selected):
                if self.stopped:
                    self.stopped_force = True
                    self.stopped_msg = _('(got {} of {})').format(a_index, len(addons_selected))
                    break

                percent = (a_index*100)//max(1, len(addons_selected))
                self.show_progress(percent,
                    '({}/{}) '.format(a_index+1, len(addons_selected))+
                    _('Updating: [{}] {}').format(a['kind'], a['name']))
                print('  [%s] %s' % (a['kind'], a['name']))

                try:
                    status, reason = self.update_one(a)
                except Exception as e:
                    status, reason = False, str(e)

                if status is None:
                    skip_count += 1
                    skipped.append((a, reason))
                    print(_('  Skipped: [{}] {} ({})').format(a['kind'], a['name'], reason))
                elif status:
                    ok_count += 1
                else:
                    fail_count += 1
                    failed.append((a, reason))
                    print(_('  Update failed: [{}] {} ({})').format(a['kind'], a['name'], reason))
        finally:
            self.hide_progress()

        s = _('Updating finished: {} updated, {} skipped, {} failed').format(ok_count, skip_count, fail_count)
        if self.stopped_force:
            s += ' '+_('stopped')+' '+self.stopped_msg
        print(s)
        msg_status(s)

        lines = [s]
        if skipped:
            lines.append('')
            lines.append(_('Skipped:'))
            for (a, reason) in skipped:
                lines.append('  [{}] {}: {}'.format(a['kind'], a['name'], reason))
        if failed:
            lines.append('')
            lines.append(_('Failed:'))
            for (a, reason) in failed:
                lines.append('  [{}] {}: {}'.format(a['kind'], a['name'], reason))
        msg_box('\n'.join(lines), MB_OK+(MB_ICONERROR if failed else MB_ICONINFO))


    def update_one(self, a):
        '''
        Updates one add-on.
        Returns (True, '') on success, (False, reason) on failure,
        (None, reason) when the add-on is skipped.
        '''
        if not a.get('compat', True):
            return (None, a.get('compat_reason', _('incompatible with current CudaText')))

        dir_to_remove = ''
        m = a.get('module', '')
        if m:
            # special update for Git repos
            m_dir = os.path.join(DIR_PY, m)
            if os.path.isdir(os.path.join(m_dir, '.git')):
                try:
                    subprocess.call(['git', 'stash', 'save'], cwd=m_dir)
                    subprocess.call(['git', 'pull'], cwd=m_dir)
                    return (True, '')
                except Exception as e:
                    return (False, _('Error running Git')+': '+str(e))
            dir_to_remove = m_dir

        url = a.get('url', '')
        if not url:
            return (None, _('no download URL'))

        fn = get_plugin_zip(url, a.get('sha256', ''))
        if fn is False:
            return (False, _('SHA-256 check failed or download aborted'))
        if not fn or not os.path.isfile(fn):
            return (False, _('cannot download file'))

        if dir_to_remove:
            do_remove_dir(dir_to_remove)

        if file_open(fn, options='/silent'):
            do_save_version(url, fn, a.get('v', ''))
            return (True, '')

        return (False, _('installation cancelled'))


    def check_cudatext_updates(self):

        check_cudatext()

    def install_from_github(self):

        do_install_from_github()

    def init_progress(self, caption=None):

        self.h_pro = dlg_proc(0, DLG_CREATE)
        dlg_proc(self.h_pro, DLG_PROP_SET, prop={
            'cap': caption or _('Download add-ons'),
            'w': 400,
            'h': 110,
            'topmost': True,
            'on_close': self.progress_close,
            })

        n = dlg_proc(self.h_pro, DLG_CTL_ADD, prop='label')
        dlg_proc(self.h_pro, DLG_CTL_PROP_SET, index=n, prop={
            'name': 'inf',
            'cap': _('Downloading...'),
            'x': 10,
            'y': 25,
            })

        n = dlg_proc(self.h_pro, DLG_CTL_ADD, prop='progressbar')
        dlg_proc(self.h_pro, DLG_CTL_PROP_SET, index=n, prop={
            'name': 'pro',
            'x': 10,
            'y': 50,
            'w': 380,
            'h': 15,
            'ex1': 0, #min
            'ex2': 100, #max
            'ex3': True, #smooth
            })

        n = dlg_proc(self.h_pro, DLG_CTL_ADD, prop='button')
        dlg_proc(self.h_pro, DLG_CTL_PROP_SET, index=n, prop={
            'name': 'btn',
            'cap': _('Cancel'),
            'x': 150,
            'w': 100,
            'y': 80,
            'on_change': self.progress_btn_click,
            })

    def show_progress(self, percent, text):

        dlg_proc(self.h_pro, DLG_CTL_PROP_SET, name='pro', prop={'val': percent,})
        dlg_proc(self.h_pro, DLG_CTL_PROP_SET, name='inf', prop={'cap': text,})
        app_proc(PROC_IDLE, False)

    def hide_progress(self):

        dlg_proc(self.h_pro, DLG_HIDE)
        dlg_proc(self.h_pro, DLG_FREE)
        self.h_pro = None

    def progress_btn_click(self, id_dlg, id_ctl, data='', info=''):

        self.stopped = True

    def progress_close(self, id_dlg, id_ctl, data='', info=''):

        self.stopped = True