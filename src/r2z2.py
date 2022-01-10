from config import *
from driver import browser
from typing import NamedTuple

class State(NamedTuple):
    bug_type: str
    p_hashes: list

class Cross_version():
    def __init__(self, br_locs, use_port=False):
        self.br_list = []

        if not isinstance(br_locs, list):
            vers = read_file(br_locs)
        else:
            vers = br_locs

        for cur_ver in vers:
            cur_ver = cur_ver.replace('\n','')
            if os.path.exists(cur_ver):
                self.br_list.append(browser(cur_ver, use_port))

        if len(self.br_list) < 2: abort()

           
    def __diff_images(self, hashes):

        states = []
        combi_execs = combinations(hashes, 2)
        for le, ri in combi_execs:
            bug_type = NON_BUG
            if is_rendering_bug(le, ri):
                bug_type = BUG 
            state_ = State(bug_type, [le, ri])
            states.append(state_)

        if len(states) == 1: return states[0]
        else: return states


    def test_html(self, html_file, comms=None, save_shot=False, pick=None):

        name = None
        bug_type = NON_BUG
        file_ = html_file.replace('.html','')

        if pick == LEFT_TWO:
            browser_list = self.br_list[0:2]
        elif pick == RIGHT_TWO:
            browser_list = self.br_list[1:3]
        else:
            browser_list = self.br_list

        img_hashes = [] 
        for br in browser_list:
            if not br.run_html(html_file): return
            if br.run_js(comms) is False: return
            if save_shot: name = '{}_{}.png'.format(file_, br.version)
            hash_v = br.screenshot_and_hash(name)
            if not hash_v: return

            for _ in range(2):
                if hash_v != br.screenshot_and_hash(name):
                    return

            img_hashes.append(hash_v)

        return self.__diff_images(img_hashes)


    def terminate(self):
        for br in self.br_list:
            br.kill_browser()


class R2Z2(threading.Thread):
    def __init__(self, id_, out_dir, br_locs):

        if os.path.exists(out_dir) or not os.path.exists(br_locs):
            print ("Wrong in output dir or browser locations")
            abort()

        threading.Thread.__init__(self)

        self.__id = id_
        self.__out_dir = out_dir
        self.__br_locs = br_locs

        self.__num_bugs = 0
        self.__num_tests = 0
        self.__num_valid_tests = 0

        self.__cur_file = ''

        self.__fuzzer = None
        self.__set_directories()

    def __del__(self):
        if self.__fuzzer is not None:
            del self.__fuzzer
            print('fuzzer is being deleted')

    def __set_directories(self):
        mkdir(self.__out_dir)
        print('\n> Output Directory : ' + self.__out_dir)

    def __get_fuzz_info(self):
        return [self.__num_tests, self.__num_valid_tests, self.__num_bugs]

    def __save_if_bug(self, state):

        bug_type = state.bug_type        
        if bug_type == NON_BUG: return

        for it in range(NUM_OF_ITER):
            state_ = self.__fuzzer.test_html(self.__cur_file)
            if not state_ or state_ != state: return

        f_name = '{}.html'.format(self.__name)
        copyfile_(self.__cur_file, f_name)

        self.__num_bugs += 1
    
    def __diff_fuzz_html(self, f_):  # rename

        self.__cur_file = f_ 

        self.__num_tests += 1
        self.__name = os.path.join(
                self.__out_dir, 
                'id:' + fill(self.__num_bugs, DIGITS))

        state = self.__fuzzer.test_html(self.__cur_file)
        if state is None:
            print ('state is None in ' + self.__cur_file)
            return

        self.__save_if_bug(state)
        self.__num_valid_tests += 1

    def run(self):

        self.__fuzzer = Cross_version(self.__br_locs)

        while True:
            queueLock.acquire()
            if not workQueue.empty():
                html_file = workQueue.get()
            else:
                queueLock.release()
                for br in self.__fuzzer.br_list:
                    br.kill_browser()
                print ('Thread R2Z2 {} is killed'.format(self.__id))
                return
            queueLock.release()

            self.__diff_fuzz_html(html_file)           

            fuzz_info[self.__id] = self.__get_fuzz_info()

            
class printThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.start_time = get_time()
        self.stop_soon = False
        self.last = -1
        self.infos = []

    def checkpoint(self):

        print_fuzz_info(self.infos, self.start_time)
        time = get_time() - self.start_time
        thput = self.infos[0] / time if time >= 1.0 else 0
        record_fuzz_info(self.r_file,
                '{}, {}, {}, {}\n'.format(
                    round(time, 2), 
                    self.infos[0], 
                    self.infos[2], 
                    round(thput, 2)))

    def run(self):
        self.r_file = os.path.join(output_dir, 'fuzz_log.txt')
        record_fuzz_info(self.r_file, 'Time(s), Tested HTMLs, CandBug, HTMLs/sec\n')

        while not self.stop_soon:
            queueLock.acquire()
            self.infos = np.sum(fuzz_info, axis=0)
            queueLock.release()
            self.checkpoint()
            if self.last == 0:
                pass
            elif self.last == self.infos[0]:
                print ('fuzzer terminate')
                abort()
            self.last = self.infos[0]
            sleep(PRINT_INTERVAL)


if __name__ == '__main__':

    set_affinity(range(int(count_cpu() / 2), count_cpu()))
    set_signal()
    os.environ["DBUS_SESSION_BUS_ADDRESS"] = "/dev/null"

    parser = argparse.ArgumentParser(description='Usage')
    parser.add_argument('-b', '--browser', required=True, type=str, help='browser config file')
    parser.add_argument('-i', '--input', required=True, type=str, help='input directory')
    parser.add_argument('-o', '--output', required=True, type=str, help='output directory')
    parser.add_argument('-j', '--job', required=False, type=int, default=4, help='number of Threads')
    args = parser.parse_args()

    fuzzThreads = []

    init_seeds = sorted(get_pathlist(args.input + '/*.html'))

    queueLock = threading.Lock()
    workQueue = Queue(len(init_seeds))

    num_proc = args.job
    fuzz_info = [[0,0,0]] * num_proc

    output_dir = args.output

    rmdir(output_dir)
    mkdir(output_dir)

    for seed in init_seeds: 
        workQueue.put(seed)

    print_thread = printThread()
    print_thread.start()

    display = virtual_display()
    display.start()

    for idx in range(num_proc):
        fuzzThreads.append(R2Z2(
            idx, os.path.join(output_dir, 'thread-' + fill(idx, 2)),
            args.browser))

    for thread in fuzzThreads:
        thread.start()
        sleep(0.5)

    for thread in fuzzThreads:
        thread.join()

    fuzz_infos = np.sum(fuzz_info, axis=0)

    print_thread.checkpoint()
    print_thread.stop_soon = True
    print_thread.join()

    display.stop()

