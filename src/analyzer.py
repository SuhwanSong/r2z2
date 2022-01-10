from config import *
from r2z2 import Cross_version
from jsondiff import diff

class Analyzer(Cross_version, threading.Thread):
    def __init__(self, id_, br_locs, out_dir):
        self.__id = id_

        threading.Thread.__init__(self)
        Cross_version.__init__(self, br_locs, use_port=True)

        self.__br_locs = br_locs
        self.__pos = self.br_list[1].version
        self.commit = get_chrome_commit_from_position(self.__pos)

        self.__out_dir = os.path.join(out_dir, self.__pos)
        mkdir (self.__out_dir)
        
        self.__diff_log = {}
        self.__logs = {}

    def get_diff_log(self):
        return self.__diff_log

    def get_log(self):
        return self.__logs

    def test_html(self, html_file, save_shot=False, paint=True, attr=False):

        name = None
        bug_type = NON_BUG
        file_ = html_file.replace('.html','')

        img_hashes = [] 
        for br in self.br_list:
            if not br.run_html(html_file): return
            if save_shot:
                name = '{}_{}.png'.format(file_, br.version)
            hash_v = br.screenshot_and_hash(name)
            if hash_v is None: return

            for i in range(1):
                if hash_v != br.screenshot_and_hash(name):
                    return
            img_hashes.append(hash_v)

        self.__diff_log = {}

        ltrees = self.br_list[0].get_all_trees(attr)
        rtrees = self.br_list[1].get_all_trees(attr)

        self.__logs = {}
        
        for typ in [DOM, ATTRS]:
            diff = DeepDiff(ltrees[typ], rtrees[typ])
            if diff:
                self.__diff_log[DOM] = diff
                self.__logs[DOM] = [tojson(ltrees[typ]), tojson(rtrees[typ])]
                return

        for typ in [STYLE, LAYOUT]:
            diff = compare_list(ltrees[typ], rtrees[typ], typ)
            for idx, dic in enumerate(diff):
                if dic:
                    self.__diff_log[typ] = DeepDiff(ltrees[typ], rtrees[typ])
                    self.__logs[typ] = [tojson(ltrees[typ]), tojson(rtrees[typ])]
                    return 

        if paint:
            lpt = self.br_list[0].paint_test(html_file)
            rpt = self.br_list[1].paint_test(html_file)
            self.__diff_log[PAINT] = {}
            for key in lpt.keys():
                diff = DeepDiff(lpt[key], rpt[key])
                if diff:
                    self.__logs[PAINT] = [tojson(lpt[key]), tojson(rpt[key])]
                    self.__diff_log[PAINT] = diff


    def get_output_dir(self):
        return self.__out_dir

    def pipeline_analysis(self, html_file):
        self.test_html(html_file, True, True, True)
        diff_log = self.get_diff_log()
        
        for key in [DOM, STYLE, LAYOUT, PAINT]:
            if  key in diff_log: return key

    def run(self):
        while True:
            queueLock.acquire()
            if not workQueue.empty():
                html_file = workQueue.get()
            else:
                queueLock.release()
                for br in self.br_list:
                    br.kill_browser()
                print ('Thread Brownie {} is killed'.format(self.__id))
                return
            queueLock.release()
           
            out_path = os.path.join(self.__out_dir, os.path.basename(html_file))
            copyfile_(html_file, out_path)

            ty = self.pipeline_analysis(out_path)
            queueLock.acquire()
            bug_typess[html_file] = ty
            queueLock.release()
            
            logs = self.get_log()
            if ty in logs:
                log = logs[ty]
            else:
                log = [[], []]


            dfiles = []
            path_noext = out_path.replace('.html', '')
            path_noext = path_noext.replace('.mht', '')
            for i, br in enumerate(self.br_list):
                dfiles.append(f'{path_noext}_{ty}_{br.version}.json')
                write_file(dfiles[-1], log[i])

            ofile = f'{path_noext}_{ty}_diff.html'
            dump_diff(dfiles[0], dfiles[1], ofile)

if __name__ == '__main__':

    set_affinity(range(int(count_cpu() / 2)))
    set_signal()

    parser = argparse.ArgumentParser(description='Usage')
    parser.add_argument('-i', '--input', required=True, type=str, help='input directory')
    parser.add_argument('-o', '--output', required=True, type=str, help='output directory')
    parser.add_argument('-b', '--br', required=False, type=str, help='culprit commit')
    args = parser.parse_args()

    bug_typess = {}

    init_seeds = []
    if os.path.isfile(args.input):
        init_seeds.append(args.input)
    else: 
        init_seeds.extend(get_pathlist(args.input + '/*.html'))
        init_seeds.extend(get_pathlist(args.input + '/*.mht'))
    queueLock = threading.Lock()
    workQueue = Queue(len(init_seeds))
    mkdir(args.output)
    if not init_seeds: sys.exit(0) 
    if not args.br:
        br_p = os.path.join(args.input, BR_PATHS)
    else:
        import bisect
        culprit_commit = int(args.br)
        tmps = read_file('data/bisect-builds-cache.csv', 'str').split(', ')
        commits = [int(commit) for commit in tmps]
        pos = bisect.bisect_left(commits, culprit_commit)

        if pos >= len(commits) and pos > 0: abort()

        fuzzer_dir = os.path.dirname(__file__)
        browser_dir = os.path.abspath(os.path.join(fuzzer_dir, os.pardir, 'chrome'))
        br_p = [] 
        for pos_ in [pos -1, pos]:
            brp = os.path.join(browser_dir, str(commits[pos_]), 'chrome')    
            download_browser(brp)
            br_p.append(brp)

    for seed in init_seeds: 
        workQueue.put(seed)

    ans = []
    num_proc = min(int(len(init_seeds) / 20 + 1), 24)

    for i in range(num_proc):
        cbt = Analyzer(i, br_p, args.output)
        ans.append(cbt)
        sleep(0.5)
    for thread in ans:
        thread.start()
    for thread in ans:
        thread.join()

    print (bug_typess)
