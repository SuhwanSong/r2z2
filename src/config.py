import os
import sys
import time
import signal
import random
import json
import argparse
import requests
import threading
import socket
import numpy as np
import re
import xlsxwriter
import subprocess

from PIL import Image
from glob import glob
from io import BytesIO
from queue import Queue
from pathlib import Path
from deepdiff import DeepDiff

from imagehash import phash
from datetime import timedelta 
from itertools import combinations
from shutil import rmtree, copyfile 
from pyvirtualdisplay import Display
from collections import Counter

hash_dict = {64: 140, 8: 0}
#hash_dict = {64: 160, 8: 0, 32: 24}
#hash_dict = {64: 180, 8: 0, 32: 16}

HASH_SIZE = os.getenv('HASH_SIZE')
if HASH_SIZE is None:
    HASH_SIZE = 64
else:
    HASH_SIZE = int(HASH_SIZE)

THRE = hash_dict[HASH_SIZE]
print (HASH_SIZE, THRE)

CHROME = 'chrome'
FIREFOX = 'firefox'


TIMEOUT = 5 << 2
NUM_OF_ITER = 4

MIN_PIXEL_DIFF = 0.5


AFL_SHM_ID = '__AFL_SHM_ID'

# Metamorphic scripts
SAVE_ALL_STATES = 'save_all_states();'
IS_SAME_DOM = 'return is_dom_same();'
IS_SAME_RT = 'return is_rt_same();'

# Fuzzing Mode
META = 'META'
CROSS = 'CROSS'

# Bug Type
NON_BUG = -1
DOM_BUG = 0
CSS_BUG = 1
STYLE_BUG = 2
LAYOUT_BUG = 3
RW_BUG = 4
RU_BUG = 5

NON_BUG = 'NON_BUG'
BUG = 'BUG'

DOM = 'DOM'
CSS = 'CSS'
STYLE = 'Style'
LAYOUT = 'Layout'
PAINT = 'Paint'
COMPOSITE = 'Composite'

DEPTH = 'DEPTH'
ATTRS = 'attrs'

FILES = 'files'
VALUES = 'values'

BUG_TYPES = {
    DOM, CSS, STYLE, LAYOUT, PAINT
}

# Others
E_HTML = '.html'
E_JS = '.js'
DIGITS = 6
PRINT_INTERVAL = 60
MAX_RUN = 2000

COMMIT_FILE = 'commit_info.txt'
BR_PATHS = 'br_paths.txt'
CHANGED_FILES = 'changed_file.txt'

CHROME_URL = 'https://chromium.googlesource.com/chromium/src/+log/'

BISECT_POINT = [-1, -1, '']

LEFT_TWO = 1
RIGHT_TWO = 2

# 

# TIME
def get_time():
    return time.time()

def sleep(t):
    time.sleep(t)

def timediff(diff):
    return timedelta(seconds=int(diff))

# FILE
def get_pathlist(dirr):
    return glob(dirr)

def mkdir(dirr):
    Path(dirr).mkdir(parents=True, exist_ok=True)

def rmdir(dirr):
    if os.path.exists(dirr):
        rmtree(dirr)

def rmfile(file_):
    if file_ is None: return
    elif os.path.exists(file_):
        os.remove(file_)

def read_file(name, typ='line'):
    if not os.path.exists(name): return

    fp = open(name, 'r')
    vers = fp.readlines()
    if typ == 'str':
        vers = ''.join(vers)
    fp.close()
    return vers

def write_file(name, text):
    fp = open(name, 'w')
    if isinstance(text, str):
        text_ = text
    elif isinstance(text, list):
        text_ = '\n'.join(text) 
    fp.write(text_)
    fp.close()

def find(path, name):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)

def basename(path):
    return os.path.basename(path)

def get_dirname_only(path):
    return os.path.basename(os.path.dirname(path))

def get_parent_dirname(path):
    return path.split('/')[-2]

def html_path_to_js(path):
    return path.replace(E_HTML, E_JS)

def get_all_files(root, ext=None):
    paths = []
    for path, subdirs, files in os.walk(root):
        for name in files:
            if ext is not None and ext not in name:
                continue
            paths.append((os.path.join(path, name)))
    return paths

def set_init_seeds(path, br_path=''):

    seeds = []
    buggy_commits = sorted(get_pathlist(path + '/*/'))

    for commit_dir in buggy_commits:
        if br_path == '':
            br_locs_file = os.path.join(commit_dir, BR_PATHS)
            print(br_locs_file)
        else:
            br_locs_file = br_path

        init_html_files = get_all_files(commit_dir, E_HTML)

        for ff in init_html_files:
            seeds.append([br_locs_file, ff])

    return seeds

# OTHERS
def abort():
    os._exit(1)

def is_chrome(project):
    return project == CHROME

def is_firefox(project):
    return project == FIREFOX

def get_phash(png, size=HASH_SIZE):
    if isinstance(png, str):
        f_ = png
    else: 
        f_ = BytesIO(png)
    image = Image.open(f_, 'r')
    hash_v = phash(image, hash_size = size)
    image.close()
    return hash_v

def distance(a,b):
    return abs(a-b)

def is_rendering_bug(a,b):
    return distance(a,b) > THRE

def fill(data, digit):
    return str(data).zfill(digit)

def virtual_display(): 
    return Display(visible = 0, size=(1024, 1024))

def set_signal():
    signal.signal(signal.SIGINT, sig_handler)

def sig_handler(signum, frame):
    abort()

def copyfile_(a,b):
    if a == b:
        pass
    else:
        copyfile(a,b)


def rand(a,b=None):
    if b is None:
        return random.randrange(a)
    else:
        return random.randrange(a, b)

def get_chrome_commit_from_position(pos):
    URL = 'https://crrev.com/' + str(pos)
    response = requests.get(URL)
    if response.status_code == 404:
        print(response.status_code)
        return 0
    else:
        a = 66
        b = 40
        print(response.text[a:a+b])
        return str(response.text[a:a+b])

def mapping(text):
    maps = {}
    for ele in text:
        z= ele.split(': ')
        if len(z) != 2: continue

        if z[0] not in maps:           
            maps[z[0]] = z[1]
        else:
            tmp = maps[z[0]]
            maps[z[0]] = tmp + ' / ' + z[1]

    return maps

def is_diff(a,b):
    diff = []
    if a != b:
        diff.append(True)
    return diff

def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def count_cpu():
    return os.cpu_count()

def set_affinity(mask):
    os.sched_setaffinity(0, mask)

def cpu_list(id_, num):

    cpus = []
    cpu_ = int(id_ * 1) 

    total_cpus = count_cpu()

    for i in range(num):
        cpus.append((cpu_ * num + i) % total_cpus)
    print (cpus)

    return cpus


def to_onekey(a,b):
    return '{}:{}'.format(a,b)

def revert_onekey(a):
    return a.split(':')


def unique_items(a, b=None):
    if b is None:
        return list(set(a))
    else:
        return list(set(a) - set(b))

def get_most_freq_value(a):
    if not a: return
    freqs = Counter(a)
    return freqs.most_common(1)[0][0]

def are_values_in_list(a,b):
    for key in a:
        if key in b:
            return True
    return False

def resub(v):
    return re.sub('\(.*\)', '(*)', v)

def per(v, num):
    return round(float(v) / num * 100, 2)

def is_subset(a,b):
    return set(a).issubset(set(b))

def is_in_any_set(a,b):
    for set_ in b:
        if is_subset(a, b[set_]):
            return True
    return False



def print_fuzz_info(fuzz_infos, start_time):
    elapsed = timediff(get_time() - start_time)
    text = '> Fuzzing Status'
    text += ': [Time] > {}'.format(elapsed)
    text += ', [test] > {}/{}'.format(
            fill(fuzz_infos[1], DIGITS), 
            fill(fuzz_infos[0], DIGITS))
    text += ', [bugs] > {}'.format(
            fill(fuzz_infos[2], DIGITS))
    print (text)

def record_fuzz_info(path, mesg):
    fp = open(path, 'a')
    fp.write(mesg)
    fp.close()

def compare_list(a,b, typ):
    diff = []

    if len(a) != len(b): return diff

    for i in range(len(a)):
        di = diff_dict(a[i], b[i], typ)
        diff.append(di)
    return diff 


def diff_dict(le, ri, typ):
    diff = {}

    for ele in ri:
        if ele not in le:
            diff[ele] = ['Undefined', ri[ele]]

    for ele in le:
        if ele not in ri:
            diff[ele] = [le[ele], 'Undefined']
            continue

        ll = le[ele]
        rr = ri[ele]

        if typ == STYLE and 'px' in ll:
            continue

        if ll != rr:
            diff[ele] = [ll, rr]
    return diff


def summarize(path):

    data_ = []
    fp = open(os.path.join(path, 'summarize.txt'), 'w')

    buggy_commits = sorted(get_pathlist(path + '/*/'))
    num_of_commits = len(buggy_commits)

    fp.write('Total Bugs: {}\n'.format(num_of_commits))

    single_bugs = 0

    for commit_dir in buggy_commits:

        commit_bug_list = []
        bug_types = sorted(get_pathlist(commit_dir + '/*/'))

        fp.write('{}: '.format(get_dirname_only(commit_dir)))

        num_of_all_bugs  = len(get_all_files(commit_dir, E_HTML))
        fp.write('{} >> '.format(num_of_all_bugs))

        for bug_type in bug_types:
            num_of_bugs = len(get_all_files(bug_type, E_HTML))
            commit_bug_list.append(num_of_bugs)
            fp.write('[{}] -> {}  '.format(get_dirname_only(bug_type), num_of_bugs))

        fp.write('\n')
        data_.append(commit_bug_list)

        if num_of_all_bugs == max(commit_bug_list):
            single_bugs += 1

    each_bug_list = np.sum(data_, axis = 1)
    each_bug_type_list = np.sum(data_, axis = 0)

    fp.write('\nNumber of Bug Types\n')
    for ele in each_bug_type_list:
        fp.write('{} '.format(ele))
    fp.write('\n')

    fp.write('\nNumber of Single Bugs: {}'.format(single_bugs))
    fp.write('\n')

    fp.close()

def build_browser(path):
    if os.path.exists(path):
        return

    fuzzer_dir = os.path.dirname(__file__)
    browser_dir = os.path.abspath(os.path.join(fuzzer_dir, os.pardir))
    browser_build = os.path.join(browser_dir, "build", "chromium_old_build.sh")

    cr_position = get_parent_dirname(path)
    commit = get_chrome_commit_from_position(cr_position)
    os.system('BRV={} {} {}'.format(cr_position, browser_build, commit))

def download_browser(path):
    if os.path.exists(path):
        return 

    fuzzer_dir = os.path.dirname(__file__)
    browser_dir = os.path.abspath(os.path.join(fuzzer_dir, os.pardir))
    browser_build = os.path.join(browser_dir, "build", "download_chrome.sh")

    cr_position = get_parent_dirname(path)
    process('{} {}'.format(browser_build, cr_position))

def is_port_open(port):
    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    location = ("127.0.0.1", port)
    result_of_check = a_socket.connect_ex(location)
    a_socket.close()
    return result_of_check == 0


class associate:
    def __init__(self):
        pass

    def all_lifts(self, freqs, union_freqs):
        most = freqs[0]
        for k in freqs:
            self.lift(union_freqs, most, k)
        

    def lift(self, union_freqs, a,b):
        x_y = set()
        x_y.add(a[0])
        x_y.add(b[0])
        c = 0
        len_ = len(union_freqs)
        for key in union_freqs:
            if x_y.issubset(union_freqs[key]):
                c += 1
        y = (len_ * c) / (a[1]*b[1])
        print ('{} & {} --> lift: {}'.format(a[0],b[0], y))

    def all_confidences(self, freqs, union_freqs):
        most = freqs[0]
        for k in freqs:
            self.confidences(union_freqs, most, k)
        

    def confidences(self, union_freqs, a,b):
        x_y = set()
        x_y.add(a[0])
        x_y.add(b[0])
        c = 0
        for key in union_freqs:
            if x_y.issubset(union_freqs[key]):
                c += 1
        y = c / a[1]
        print ('{} & {} --> confidences: {}'.format(a[0],b[0], y))


def write_paint_diff(name, data, typ):
    if data is None: return
    x = data.to_json()
    x = json.loads(x)
    x = json.dumps(x, indent=4)
    write_file(name.replace('.xlsx', '_{}.json'.format(typ)), x)


def write_diff(name, data, tags):
    workbook = xlsxwriter.Workbook(name)
    normal_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'})
    merge_format = workbook.add_format({
        'bold': 1,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': 'yellow'})

    for compo in data:
        if not compo: continue
        worksheet = workbook.add_worksheet(compo)
        worksheet.merge_range('B1:C1', 'v1', merge_format)
        worksheet.merge_range('D1:E1', 'v2', merge_format)
        worksheet.write(1, 0, 'tag', normal_format)
        pp = ['property', 'value']
        for i in range(4):
            worksheet.write(1, i + 1, pp[i % len(pp)], normal_format)
            worksheet.set_column(1, i + 1, 15)

        for i, eles in enumerate(data[compo]):
            values = data[compo][eles]
            for key in values:
                logs = [tags[int(eles)], key, values[key][0], key, values[key][1]] 
                worksheet.write_row(2 + i, 0, logs, normal_format)
    workbook.close()

def process(cmd):
    if isinstance(cmd, str):
        cmd = cmd.split(' ')
    return subprocess.run(cmd)

def jaccard_distance(a,b):
    a = set(a)
    b = set(b)
    return len(a & b) / len(a | b)
