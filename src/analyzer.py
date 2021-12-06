from config import *
from r2z2 import Cross_version

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
        self.__diff_log

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
            


class CBT(threading.Thread):
    def __init__(self, id_, out_dir, br_locs, ref, ppl=None):
        threading.Thread.__init__(self)

        self.__id = id_
        self.an = Analyzer(br_locs, out_dir, ref)

        self.ppl = ppl


    def run(self):
        while True:
            queueLock.acquire()
            if not workQueue.empty():
                html_file = workQueue.get()
            else:
                queueLock.release()
                for br in self.an.br_list:
                    br.kill_browser()
                print ('Thread Brownie {} is killed'.format(self.__id))
                return
            queueLock.release()


            hashes = self.an.cross_browser_test(html_file)
            if hashes is not None:
                queueLock.acquire()
                bug_list[html_file] = hashes
                queueLock.release()

                f_name = basename(html_file)
                output_dir = self.an.get_output_dir()

                file_path = os.path.join(output_dir, f_name)
                if html_file != file_path:
                    copyfile_(html_file, file_path)
                for br in self.an.br_list:
                    file_ = html_file.replace('.html','') 
                    name = '{}_{}_ahem.png'.format(file_, br.version)

                    tmp_file_path = os.path.join(output_dir, basename(name))
                    if name != tmp_file_path:
                        copyfile_(name, tmp_file_path)

                if self.ppl:
                    ty = self.an.pipeline_analysis(html_file, True)
                    queueLock.acquire()
                    bug_typess[html_file] = ty
                    queueLock.release()




if __name__ == '__main__':

    set_affinity(range(int(count_cpu() / 2)))
    set_signal()

    parser = argparse.ArgumentParser(description='Usage')
    parser.add_argument('-i', '--input', required=True, type=str, help='input directory')
    parser.add_argument('-o', '--output', required=True, type=str, help='output directory')
    parser.add_argument('-r', '--ref', required=False, default='', type=str, help='reference browser path')
    parser.add_argument('-b', '--br', required=False, default='', type=str, help='browser path')
    parser.add_argument('--summary', action="store_true", default=False, help='save summary')
    parser.add_argument('--paint', action="store_true", default=False, help='use paint')
    parser.add_argument('--eval', action="store_true", default=False, help='use paint')
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
    else:
        if args.eval:
            fuzzer_dir = os.path.dirname(__file__)
            browser_dir = os.path.abspath(os.path.join(fuzzer_dir, os.pardir))
            commits = read_file('data/bisect-builds-cache.csv', 'str').split(', ')
            tmp_path = os.path.join(browser_dir, CHROME)
            pos = basename(args.input)
            down_ver = int(pos) - 1
            up_ver = int(pos)
            while not str(down_ver) in commits:
                down_ver -= 1
            while not str(up_ver) in commits:
                up_ver += 1

            br_p = ['chrome/{}/chrome'.format(down_ver), 
                    'chrome/{}/chrome'.format(up_ver)]
            write_file('/tmp/xxxx00000', '\n'.join(br_p))
            for pp in br_p:
                download_browser(pp)
            br_p = '/tmp/xxxx00000'
                
        else:
            br_p = args.br
        an = Analyzer(br_p, args.output, args.ref)
        for html_file in init_seeds:
            xx=  an.pipeline_analysis(html_file, True)
            print (xx)
            if xx.replace(STYLE, 'CSS') == get_parent_dirname(args.input):
                print ('correct')
            
            diff_log = an.get_diff_log()
            print (diff_log[COMPOSITE])
        
        abort()




    for seed in init_seeds: 
        workQueue.put(seed)

    ans = []
    num_proc = 1
    if num_proc == 1:
        num_proc = min(int(len(init_seeds) / 20 + 1), 24)

    for i in range(num_proc):
        cbt = CBT(i, args.output, br_p, args.ref, args.paint)
        cbt.start()
        ans.append(cbt)
        sleep(2)

        pos = cbt.an.br_list[1].version
        commit = cbt.an.commit

    copyfile_(br_p, os.path.join(args.output, pos, BR_PATHS))
    for thread in ans:
        thread.join()

    
    print (bug_list)
    print (bug_typess)
    if bug_typess:
        bb = list(bug_typess.values())[0]
    if args.summary and bug_list:
        with open(os.path.join(args.output, 'summary.txt'), "a") as fp:
            fp.write('REALBUG: {}, {} {} by CBT\n'.format(pos, commit, bb))
        write_file(os.path.join(args.output, pos, 'result.txt'), '\n'.join(bug_list.keys()) + '\n')
