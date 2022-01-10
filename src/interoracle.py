from config import *
from r2z2 import Cross_version

class InterOracle(Cross_version, threading.Thread):
    def __init__(self, id_, br_locs, out_dir, ref):
        vers = read_file(br_locs)
        vers.append(ref)

        threading.Thread.__init__(self)
        Cross_version.__init__(self, vers, use_port=True)

        self.__id = id_
        self.__br_locs = br_locs
        self.__pos = self.br_list[1].version
        self.commit = get_chrome_commit_from_position(self.__pos)

        self.__out_dir = os.path.join(out_dir, self.__pos)
        self.__diff_log = ''

    def get_diff_log(self):
        return self.__diff_log

    def get_output_dir(self):
        return self.__out_dir

    def cross_browser_test(self, html_file, use_ahem=True):
        logs = []
        for br in self.br_list[1:]:
            css = []
            if not br.run_html(html_file): return
            tree = br.get_all_trees()
            try:
                css = br.get_all_css_rules()
                    
            except Exception as e:
                print (html_file, e)
                pass
            logs.append([tree[DOM], css])
        if len(logs) != 2: return 
        diff = DeepDiff(logs[0], logs[1])
        if not diff: pass 
        else: return

        file_text = read_file(html_file, 'str')

        # no doctype (quirk)
        #if file_text.startswith('<!doctype html>\n'):
        #    write_file(html_file, file_text.replace('<!doctype html>\n',''))

        hashes = []
        for br in self.br_list:
            if not br.run_html(html_file): return
            file_ = html_file.replace('.html','') 
            name = '{}_{}.png'.format(file_, br.version)
            hash_v = br.screenshot_and_hash(name)
            if use_ahem:
                br.run_js('se = document.createElement(\'script\'); ' +  
                        'se.src = \'/tmp/ahem.js\'; ' +
                        'document.head.appendChild(se); ')
                br.run_js('set_font();')
                name = '{}_{}_ahem.png'.format(file_, br.version)
                hash_v = br.screenshot_and_hash(name)
            if hash_v is None: break
            hashes.append(hash_v)
        
        if len(hashes) != 3: return

        ref = hashes[0] - hashes[1]

        if ref >= THRE and hashes[0] - hashes[2] <= (THRE // 16):
            return [ref, hashes[0] - hashes[2]]

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

            hashes = self.cross_browser_test(html_file)
            if hashes:
                queueLock.acquire()
                bug_list[html_file] = hashes
                queueLock.release()

                f_name = basename(html_file)
                output_dir = self.get_output_dir()
                mkdir(output_dir)
                brpath = os.path.join(output_dir, BR_PATHS)
                if not os.path.exists(brpath):
                    copyfile_(br_p, brpath)

                file_path = os.path.join(output_dir, f_name)
                copyfile_(html_file, file_path)
                for br in self.br_list:
                    file_ = html_file.replace('.html','') 
                    name = '{}_{}_ahem.png'.format(file_, br.version)

                    tmp_file_path = os.path.join(output_dir, basename(name))
                    if name != tmp_file_path:
                        copyfile_(name, tmp_file_path)



if __name__ == '__main__':

    set_affinity(range(int(count_cpu() / 2)))
    set_signal()

    parser = argparse.ArgumentParser(description='Usage')
    parser.add_argument('-i', '--input', required=True, type=str, help='input directory')
    parser.add_argument('-o', '--output', required=True, type=str, help='output directory')
    parser.add_argument('-r', '--ref', required=False, default='', type=str, help='reference browser path')
    parser.add_argument('-b', '--br', required=False, default='', type=str, help='browser path')
    parser.add_argument('--paint', action="store_true", default=False, help='use paint')
    args = parser.parse_args()

    bug_typess = {}

    bug_list = {}

    init_seeds = sorted(get_pathlist(args.input + '/*.html'))
    queueLock = threading.Lock()
    workQueue = Queue(len(init_seeds))
    mkdir(args.output)
    if not init_seeds:
        abort()

    if not args.br:
        br_p = os.path.join(args.input, BR_PATHS)

    for seed in init_seeds: 
        workQueue.put(seed)

    if not os.path.exists('/tmp/ahem.js'): 
        copyfile_('src/ahem.js', '/tmp/ahem.js')

    ans = []
    num_proc = min(int(len(init_seeds) / 20 + 1), 24)

    for i in range(num_proc):
        cbt = InterOracle(i, br_p, args.output, args.ref)
        ans.append(cbt)
        sleep(1)
    for thread in ans:
        thread.start()
    for thread in ans:
        thread.join()

    print (bug_list)
