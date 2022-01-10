from config import *
from driver import browser
from r2z2 import Cross_version

class Bisector(threading.Thread):
    def __init__(self, id_, start_pos, end_pos, br_type):
        threading.Thread.__init__(self)

        self.__id_ = id_
        self.__bisector = None
        self.__br_type = br_type

        self.__start_pos = start_pos
        self.__end_pos = end_pos

    def __save_bisect_info(self, s, e, html_file, pick):

        left = br_lists[s]
        right = br_lists[e]

        begin_ = get_parent_dirname(left)
        end_ = get_parent_dirname(right)

        dir_commit = os.path.join(output_dir, end_)

        doneLock.acquire()  ## LOCK

        bisected_list[html_file] += 1

        if not os.path.exists(dir_commit):
            mkdir(dir_commit)

        b_commit_file = os.path.join(dir_commit, COMMIT_FILE)
        br_paths_file = os.path.join(dir_commit, BR_PATHS)

        if not os.path.exists(b_commit_file):
            good = get_chrome_commit_from_position(begin_)
            bad = get_chrome_commit_from_position(end_)

            write_file(b_commit_file, 
                    '{}{}..{}\n'.format(CHROME_URL, good, bad))

            write_file(br_paths_file,
                    [left, right])

        bug_path = dir_commit
        if bug_path not in num_bugs:
            num_bugs[bug_path] = 0

        num_bugs[bug_path] += 1
        num = num_bugs[bug_path]
        f_name = os.path.join(bug_path, 'id:' + fill(num, DIGITS))  
        js_file = html_path_to_js(html_file)
        copyfile_(html_file, f_name + E_HTML)
        doneLock.release() ## RELEASE


    def __bisecting(self, html_file):

        if html_file not in bisected_list:
            bisected_list[html_file] = 0

        cc = 0
        comms = read_file(html_path_to_js(html_file))
        states = self.__bisector.test_html(html_file, comms)

        if states is None: 
            print('[{}] state is None: {}'.format(self.__id_, html_file))
            return

        s_e = states[1] 
        s_m = states[0]
        m_e = states[2]

        if s_e.bug_type == NON_BUG: 
#            print('{} is Not Bug from {} to {}'.format(html_file,
#                    self.__start_pos, self.__end_pos))
            return

        if s_m.bug_type != NON_BUG:
            if distance(self.__start_pos, self.__mid_pos) == 1:
                s_m = self.__bisector.test_html(html_file, comms)[0]
                self.__save_bisect_info(
                        self.__start_pos, 
                        self.__mid_pos, html_file, LEFT_TWO)
            else:
                queueLock.acquire()

                key = to_onekey(self.__start_pos, self.__mid_pos)
                if key not in Queues:
                    Queues[key] = Queue() 

                Queues[key].put(html_file)
                queueLock.release()
        
        if m_e.bug_type != NON_BUG:
            if distance(self.__mid_pos, self.__end_pos) == 1:
                m_e = self.__bisector.test_html(html_file, comms)[2]
                self.__save_bisect_info(
                        self.__mid_pos, 
                        self.__end_pos, html_file, RIGHT_TWO)
            else:
                queueLock.acquire()
                key = to_onekey(self.__mid_pos, self.__end_pos)
                if key not in Queues:
                    Queues[key] = Queue() 

                Queues[key].put(html_file)
                queueLock.release()

    def run(self):

        queue = None
        max_key = ''

        while True:
            queueLock.acquire()

            if not Queues: 
                queueLock.release()
                print('All Done!')
                break

            elif queue is None or queue.empty():

                print ('Queue is Empty')
                if max_key in Queues:
                    del Queues[max_key]

                if not Queues: 
                    queueLock.release()
                    print('All Done!')
                    break

                max_key = random.choice(list(Queues.keys()))
                
                for key in Queues:
                    length = len(Queues[key].queue)
                    if length > len(Queues[max_key].queue):
                        max_key = key

                queue = Queues[max_key]
                queueLock.release()

                max_ = revert_onekey(max_key)
                
                self.__start_pos = int(max_[0])
                self.__end_pos = int(max_[1])

                mt = int((self.__start_pos + self.__end_pos) / 2)
                self.__mid_pos = mt

                start_path = br_lists[self.__start_pos]
                mid_path = br_lists[self.__mid_pos]
                end_path = br_lists[self.__end_pos]
                
                br_locs = [
                        start_path,
                        mid_path,
                        end_path
                        ]
 
                buildLock.acquire()
                for tmp_br_path in br_locs:
                    for i in range(10):
                        download_browser(tmp_br_path)
                    if build_mode:
                        build_browser(tmp_br_path)

                buildLock.release()
    
                print (br_locs)
                if self.__bisector:
                    self.__bisector.terminate()    

                self.__bisector = Cross_version(br_locs) 
                continue

            hf = queue.get()
            queueLock.release()

            doneLock.acquire()  ## LOCK

            doneLock.release() ## RELEASE

            print(self.__start_pos, self.__mid_pos, self.__end_pos, hf, self.__id_)
            self.__bisecting(hf)

#        self.__display.stop()


if __name__ == '__main__':

    set_affinity(range(int(count_cpu() / 2)))
    set_signal()
    os.environ["DBUS_SESSION_BUS_ADDRESS"] = "/dev/null"

    parser = argparse.ArgumentParser(description='Usage')
    parser.add_argument('-i', '--input', required=True, type=str, help='input directory')
    parser.add_argument('-o', '--output', required=True, type=str, help='output directory')
    parser.add_argument('-b', '--browser', required=False, type=str, help='browser config file')
    parser.add_argument('-j', '--job', required=False, type=int, default=4, help='number of Threads')
    parser.add_argument('-t', '--test', required=False, type=int, default=1, help='number of commits')
    parser.add_argument('--build', action="store_true", default=False, help='')
    parser.add_argument('--download', action="store_true", default=False, help='')
    args = parser.parse_args()

    fuzzThreads = []

    display = virtual_display()
    display.start()
    
    br_type = CHROME

    init_seeds = get_all_files(args.input, E_HTML)

    doneLock = threading.Lock()
    queueLock = threading.Lock()
    buildLock = threading.Lock()

    print ('Total number of init bugs are {}'.format(len(init_seeds)))

    num_proc = args.job

    if num_proc == 1:
        num_proc = min(int(len(init_seeds) / 30 + 1), 24)

    br_path = os.path.join(args.input, BR_PATHS)
    commits = read_file(br_path) if os.path.exists(br_path) else read_file(args.browser)
    start_commit = int(get_parent_dirname(commits[0]))
    end_commit = int(get_parent_dirname(commits[1]))

    fuzzer_dir = os.path.dirname(__file__)
    browser_dir = os.path.abspath(os.path.join(fuzzer_dir, os.pardir))
    tmp = sorted(get_pathlist(browser_dir + "/{}/*/{}".format(br_type, br_type)))

    br_lists = []
    build_mode = args.build
    
    if build_mode:
#        num_proc = 1
        set_affinity(range(count_cpu()))
        tmp_path = os.path.join(browser_dir, br_type)
        for idx in range(start_commit, end_commit + 1):
            str_idx = str(idx)
            br_lists.append(os.path.join(tmp_path, str_idx, br_type))

    else:
        commits = read_file('data/bisect-builds-cache.csv', 'str').split(', ')
        tmp_path = os.path.join(browser_dir, br_type)
        for commit in commits:
            vv = int(commit)
            if start_commit <= vv and vv <= end_commit:
                br_lists.append(os.path.join(tmp_path, commit, br_type))


    output_dir = args.output
    mkdir(output_dir)

    bb = 0
    ee = len(br_lists) - 1

    Queues = {}

    bisected_list = {}
    num_bugs = {}

    key = to_onekey(bb,ee)

    for seed in init_seeds:
        if key not in Queues:
            Queues[key] = Queue()
        Queues[key].put(seed)

    bisectThreads = []

    for idx in range(num_proc):
        bisectthread = Bisector(idx, bb, ee, br_type)
        bisectThreads.append(bisectthread)
        bisectthread.start()
        sleep(1)

    print ('>>>>')

    for bisect in bisectThreads:
        bisect.join()

    display.stop()

    if not build_mode:
        write_tmp_buffer = []
        for k, v in bisected_list.items():
            if v > 0: write_tmp_buffer.append('file: {}'.format(k))

        write_file(os.path.join(output_dir, 'bisected_list.txt'), write_tmp_buffer)
