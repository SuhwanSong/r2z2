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

        self.__cur_source = ''
        self.__diff_log = {}
           
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

    def __diff_trees(self, lt, rt):
        is_ = False
        self.bug_type_is = ''
        for typ in [DOM, ATTRS]:
#            print (lt[typ], rt[typ])
            diff = DeepDiff(lt[typ], rt[typ])
            if diff:
                print (diff)
        for typ in [STYLE, LAYOUT]:
            diff = compare_list(lt[typ], rt[typ], typ)
            self.__diff_log[typ] = {}
            for idx, dic in enumerate(diff):
                if dic:
                    is_ = True
                    self.__diff_log[typ][idx] = dic
            if is_: 
                self.bug_type_is = typ
                break
        return is_

    def get_diff_log(self):
        return self.__diff_log


    def test_html(self, html_file, comms=None, save_shot=False, pick=None, analysis=False, paint=True, attr=False):

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
            if not save_shot and analysis: continue
            elif save_shot:
                name = '{}_{}.png'.format(file_, br.version)
            hash_v = br.screenshot_and_hash(name)
            if hash_v is None: return

            for i in range(1):
                if hash_v != br.screenshot_and_hash(name):
                    return
            img_hashes.append(hash_v)

        if not analysis:
            return self.__diff_images(img_hashes)

        self.__diff_log = {}

        ltrees = browser_list[0].get_all_trees(attr)
        rtrees = browser_list[1].get_all_trees(attr)
#        lcss = browser_list[0].get_all_css_rules()
#        rcss = browser_list[1].get_all_css_rules()
#
#        print (lcss, rcss)
        self.tags = rtrees[DOM]

        if self.__diff_trees(ltrees, rtrees):
            return self.__diff_log

        browser_list[0].get_paint()
        browser_list[1].get_paint()

        if paint:
            lpt = browser_list[0].xxx(html_file)
            rpt = browser_list[1].xxx(html_file)
            if len(lpt[0]) != len(rpt[0]):
                self.__diff_log[COMPOSITE] = DeepDiff(lpt[0], rpt[0])
                print ('composite bug')
                self.bug_type_is = COMPOSITE
                return 
#            else:
#                diff = DeepDiff(lpt[1], rpt[1])
#                if diff:
#                    self.__diff_log[PAINT] = diff
#                    print ('paint bug')
#                else:
#                    diff = DeepDiff(lpt[2], rpt[2])
#                    self.__diff_log[COMPOSITE] = diff
#                    print ('composite bug')
            diff = DeepDiff(lpt[1], rpt[1])
            if diff:
                self.__diff_log[PAINT] = diff
                print ('paint bug')
                self.bug_type_is = PAINT
            diff = DeepDiff(lpt[3], rpt[3])
            if diff:
                self.__diff_log[PAINT] = diff
                print ('paint bug')
                self.bug_type_is = PAINT
            else:
                self.__diff_log[COMPOSITE] = DeepDiff(lpt[2], rpt[2])
                self.bug_type_is = COMPOSITE
                print ('composite diff')
                

            return 

    def terminate(self):
        for br in self.br_list:
            br.kill_browser()


class Analyzer(Cross_version):
    def __init__(self, br_locs, out_dir, ref=''):
        vers = read_file(br_locs)
        if ref != '':
            vers.append(ref)

        Cross_version.__init__(self, vers, use_port=True)

        self.summary = ''
        self.trees_list = {}
        self.css_list = {}

        self.__br_locs = br_locs
        self.__pos = self.br_list[1].version
        self.commit = get_chrome_commit_from_position(self.__pos)

        self.__out_dir = os.path.join(out_dir, self.__pos)
        mkdir(self.__out_dir)

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
        if not diff:
            print ('{} is good to use cross browser testing'.format(html_file))
        else:
            return

        file_text = read_file(html_file, 'str')
#        # doctype (standard)
#        if not file_text.startswith('<!doctype html>\n'):
#            file_text = '<!doctype html>\n' + file_text
#            write_file(html_file, file_text)

        # no doctype (quirk)
        if file_text.startswith('<!doctype html>\n'):
            write_file(html_file, file_text.replace('<!doctype html>\n',''))

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

    def __cross_browser_testing(self, html_files, use_ahem=True):

        bug_list = {}

        for html_file in html_files:
            p = self.cross_browser_test(html_file)
            if p is not None:
                bug_list[html_file] = p

        if bug_list:
            print (bug_list)
            print ('-- CBT Test! Bug is introduced in commit {}'.format(self.__pos))
            self.summary += 'REALBUG: {}, {} by CBT\n'.format(self.__pos, self.commit)

        return bug_list

    def __get_data(self, html_file, test_diff=True):
        all_ = []
        tree = []
        css = []
        for br in self.br_list[0:2]:
            if not br.run_html(html_file): return
            tree = br.get_all_trees(True)
            try:
                css = br.get_all_css_rules()
            except Exception as e:
                print (html_file, e)
                pass
            all_.append([tree[DOM], css])
        if test_diff:
            diff = DeepDiff(all_[0], all_[1])
            if diff:
                print (diff)
                print (html_file, ' is not a bug [CSS NOT MATCH]')
        return tree, css

    def __get_dataset(self, html_files):
        # Obtain dom tree info from every inputs
        num = len(html_files)
        for i, html_file in enumerate(html_files):
            if i % 5 == 0: 
                print ('[DOM & CSS] processing inputs {}%'.format(per(i, num)))

            tree, css = self.__get_data(html_file, False)
            if tree:
                self.trees_list[html_file] = tree
            if css:
                self.css_list[html_file] = css

        print ('[DOM & CSS] processing inputs 100%')

    def __map_dom_item(self, tree):
        return set(unique_items(tree[DOM],['html', 'head', 'body', 'style', 'link']))

    def __map_css_item(self, css):
        tmp = []
        for ith in css:
            ith.pop('background-color', None)
            u_css_props = unique_items(ith)
            tmp.extend(u_css_props)
        return set(unique_items(tmp))

    def __process_dom_data(self):
        dom_uniqs = {}
        dom_uniq_list = []
        for html_file in self.trees_list:
            dom_uniqs[html_file] = self.__map_dom_item(self.trees_list[html_file])
            dom_uniq_list.extend(dom_uniqs[html_file])
        return dom_uniqs, dom_uniq_list

    def __process_css_data(self):
        css_uniqs = {}
        css_uniq_list = []
        if self.css_list:
            for html_file in self.css_list:
                css_uniqs[html_file] = self.__map_css_item(self.css_list[html_file])
                css_uniq_list.extend(list(css_uniqs[html_file]))
        return css_uniqs, css_uniq_list

    def __analyze_commit(self, minimize=False):
        src_dir = 'chrome/src'
        wpt_dir = os.path.join(src_dir, 'third_party/blink/web_tests')
        ref_dir = os.path.join(self.__out_dir, 'ref')
        changed = os.path.join(ref_dir, CHANGED_FILES)
        mkdir(ref_dir)

        process('./tools/git_file_diff.sh {} {}'.format(self.commit, os.path.abspath(changed)))
        files = read_file(changed)

        org_files = {}
        ref_files = {}
        for file_ in files:
            file_ = file_[:-1]
            if 'crash' in file_:
                continue

            elif file_.endswith(E_HTML) or file_.endswith('.png') or file_.endswith('.txt'):
                org_files[file_] = 'HTML'
                bn = basename(file_.replace('-expected', '').replace('.png', E_HTML).replace('.txt', E_HTML))
                path = find(wpt_dir, bn)
                if path is None: continue
                print (path)
                ref_files[path] = 1

            elif file_.endswith('TestExpectations'):
                # TODO
                org_files[file_] = 'Expectation'
        for ref in ref_files:     
            process('#./tools/wpt run --binary {} --webdriver-binary {} {} {}'.format())
            pass

#        if not org_files:
#            print ('-- No reference inputs!! Bug is introduced in commit {}'.format(self.__pos))
#            self.summary += 'REALBUG: {}, {}\n'.format(self.__pos, self.commit)
#            return {}

        return ref_files

    def __analyze_commit_negative(self, html_files, ref_files):
        self.__get_dataset(ref_files.keys())
        dom_uniqs, dom_uniq_list = self.__process_dom_data()
        css_uniqs, css_uniq_list = self.__process_css_data()
        uniq_list = dom_uniq_list + css_uniq_list

        uniqs = {}
        for key in dom_uniqs:
            uniqs[key] = dom_uniqs[key]
            if key in css_uniqs:
                uniqs[key] = uniqs[key] | css_uniqs[key]
                print (css_uniqs[key])

        candi_uniqs = {}
        print('candidate maps')
        for html_file in html_files:
            print ('Test ', html_file)
            tree, css = self.__get_data(html_file)
            dom_map = self.__map_dom_item(tree)
            css_map = self.__map_css_item(css)
            for key in ref_files:
#                dis = jaccard_distance((dom_map | css_map), uniqs[key])
#                if dis >= 0.2:
#                    print ('{} is not bug'.format(html_file))

                common = (dom_map | css_map) & uniqs[key]
                print ('common: ', common)
                if len(common) > 1:
                    print ('{} is not bug'.format(html_file))
                else:
                    candi_uniqs[html_file] = common
        if candi_uniqs:
            print ('-- Bug is introduced in commit {}'.format(self.__pos))
            self.summary += 'BUG: {}, {}\n'.format(self.__pos, self.commit)
        return candi_uniqs
       
    def __analyze_dom(self, html_files):
        print ('The number of inputs is {}'.format(len(html_files)))
        self.cbt_bug_list = {}
        if len(self.br_list) == 3:
            self.cbt_bug_list = self.__cross_browser_testing(html_files)

        if self.cbt_bug_list: 
            return self.cbt_bug_list

    def __diff_analysis(self, html_files, paint_check=False):
        for html_file in html_files:
            self.test_html(html_file, pick=LEFT_TWO, save_shot=True, analysis=True, paint=paint_check, attr=True)
            diff_log = self.get_diff_log()

            if PAINT in diff_log:
                write_paint_diff(os.path.join(self.__out_dir, 
                        basename(html_file).replace(E_HTML, '.xlsx')), diff_log[PAINT], PAINT)
            elif COMPOSITE in diff_log:
                write_paint_diff(os.path.join(self.__out_dir, 
                        basename(html_file).replace(E_HTML, '.xlsx')), diff_log[COMPOSITE], COMPOSITE)
            else:
                write_diff(os.path.join(self.__out_dir, 
                        basename(html_file).replace(E_HTML, '.xlsx')), 
                        diff_log, self.tags)

    def pipeline_analysis(self, html_file, paint_check=False):
        self.test_html(html_file, pick=LEFT_TWO, save_shot=True, analysis=True, paint=paint_check, attr=True)
        diff_log = self.get_diff_log()
        
        if PAINT in diff_log:
            write_paint_diff(os.path.join(self.__out_dir, 
                    basename(html_file).replace(E_HTML, '.xlsx')), diff_log[PAINT], PAINT)

        elif COMPOSITE in diff_log:
            write_paint_diff(os.path.join(self.__out_dir, 
                    basename(html_file).replace(E_HTML, '.xlsx')), diff_log[COMPOSITE], COMPOSITE)
        else:
            write_diff(os.path.join(self.__out_dir, 
                    basename(html_file).replace(E_HTML, '.xlsx')), 
                    diff_log, self.tags)
        return self.bug_type_is

    def start_analysis(self, html_files, paint_check=False):
        self.not_bug_list = {}
        bug_files = self.__analyze_dom(html_files)
        if isinstance(bug_files, dict):
            bug_files = bug_files.keys()
        if self.not_bug_list:
            write_file(os.path.join(self.__out_dir, 'not_bug_list.txt'), '\n'.join(self.not_bug_list.keys()))
        if bug_files:
            write_file(os.path.join(self.__out_dir, 'result.txt'), '\n'.join(bug_files) + '\n')
            self.__diff_analysis(bug_files, paint_check)
            

class Brownie(threading.Thread):
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
            state_ = self.__fuzzer.test_html(self.__cur_file, self.__comms, False)
            if state_ is None: return
            elif state_ != state: return

        f_name = '{}.html'.format(self.__name)
        copyfile_(self.__cur_file, f_name)

        if self.__comms is not None:
            write_file(f_name.replace('.html', '.js'), self.__comms)

        self.__num_bugs += 1
    
    def __diff_fuzz_html(self, f_):  # rename

        self.__cur_file = f_ 

        self.__num_tests += 1
        self.__name = os.path.join(
                self.__out_dir, 
                'id:' + fill(self.__num_bugs, DIGITS))

        self.__comms = None
        state = self.__fuzzer.test_html(self.__cur_file, self.__comms)
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
                print ('Thread Brownie {} is killed'.format(self.__id))
                return
            queueLock.release()

            self.__diff_fuzz_html(html_file)           

            fuzz_info[self.__id] = self.__get_fuzz_info()

            
class printThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.start_time = get_time()
        self.stop_soon = False
        self.last = 0
        self.infos = []

    def checkpoint(self, now=False):
        if now:
            self.infos = np.sum(fuzz_info, axis=0)

        print_fuzz_info(self.infos, self.start_time)
        if self.__ii % 5 == 0 or now:
            record_fuzz_info(self.r_file,
                    '{}, {}, {}\n'.format(
                            get_time() - self.start_time, 
                            self.infos[0], self.infos[2]))
        self.__ii += 1

    def run(self):

        self.__ii = 0
        self.r_file = os.path.join(output_dir, 'fuzz_log.txt')
        record_fuzz_info(self.r_file, 'Time, Tested HTMLs, CandBug\n')

        while not self.stop_soon:
            queueLock.acquire()
            self.infos = np.sum(fuzz_info, axis=0)
            queueLock.release()

#            if tmp == self.infos:
#                break
#            else:
#                self.infos = tmp

            self.checkpoint()
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
        brownie = Brownie(
            idx, os.path.join(output_dir, 'thread-' + fill(idx, 2)),
            args.browser)
        fuzzThreads.append(brownie)
        brownie.start()
        sleep(2)

    for thread in fuzzThreads:
        thread.join()

    fuzz_infos = np.sum(fuzz_info, axis=0)

    print_thread.checkpoint(True)
    print_thread.stop_soon = True
    print_thread.join()

    display.stop()

