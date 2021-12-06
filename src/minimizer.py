import re
from config import *
from driver import browser
from bs4 import BeautifulSoup
from r2z2 import Cross_version


class Minimizer(threading.Thread):
    def __init__(self, mode, is_overwrite, output_dir, aggr_mode):
        threading.Thread.__init__(self)

        self.__fuzzer = None
        self.__tmp_file = None
        self.__trim_file = None
        self.__overwrite = is_overwrite
        self.__output_dir = output_dir
        self.__aggr_mode = aggr_mode

    def __free_all(self):
        rmfile(self.__tmp_file)
        rmfile(self.__trim_file)
        if self.__fuzzer is not None:
            self.__fuzzer.terminate()

    def __get_file_for_trimming(self, html_file):
        in_html = read_file(html_file, 'str')

        self.__comms = []
        self.__html_file = html_file
        self.__js_file = html_file.replace('.html', '.js')
        self.__trim_file = os.path.join(os.path.dirname(html_file), 
                '.trim' + os.path.basename(html_file))
        self.__tmp_file = os.path.join(os.path.dirname(html_file), 
                '.tmp' + os.path.basename(html_file))

        if in_html is None:
            return
        self.__min_html = in_html.split('\n')

        self.__comms = read_file(self.__js_file)
        
        self.__init_state = self.__fuzzer.test_html(html_file, self.__comms)
        return 1

    def __minimize_line(self):
        if isinstance(self.__min_html, str):
            self.__min_html = self.__min_html.split('\n')
        self.__in_html = self.__min_html
        in_html_num_lines = len(self.__in_html)
        self.__min_indices = range(in_html_num_lines) 
        print('> Initial line number: {}'.format(in_html_num_lines))

#        self.__min_html = '\n'.join(self.__min_html)

        try_indices = []
        for i, line in enumerate(self.__in_html):
            try_indices.append(i)

        trim_sizes = [ pow(2, i) for i in range(7,-1,-1) ] # 128,64,32,16,8,4,2,1
        trim_sizes = [x for x in trim_sizes if x < in_html_num_lines]

        for trim_size in trim_sizes:
            print('> Setting trim size: {}'.format(trim_size))
            for offset in range(0, len(try_indices), trim_size):
                if try_indices[offset] not in self.__min_indices:
                    continue
                print('> Current line number: {}, progress: {}%'.format(
                            len(self.__min_html), 
                            int(float(offset) * 100 / len(try_indices))))

                trim_range = range(offset, min(offset + trim_size, len(try_indices)))
                trim_indices = [ try_indices[i] for i in trim_range ]

                min_html = []
                min_indices = []
                for i, line in enumerate(self.__in_html):
                    if i not in trim_indices and i in self.__min_indices:
                        min_html.append(line + '\n')
                        min_indices.append(i)

                write_file(self.__trim_file, min_html)

                if self.__is_reproducible(self.__aggr_mode):
                    self.__min_html = min_html
                    self.__min_indices = min_indices
                    write_file(self.__tmp_file, min_html)
      
    def __minimize_element(self):
        print("> minimize element!")
        min_html = ''.join(self.__min_html)
        soup = BeautifulSoup(min_html, "lxml")
        elements = soup.find_all()
        for idx in range(len(elements)-1, 2, -1):
            soup = BeautifulSoup(min_html, "lxml")
            elements = soup.find_all()
            re = str(elements[idx])
            tmp_text = str(soup).replace(re,"")

            write_file(self.__trim_file, tmp_text)

            if self.__is_reproducible(self.__aggr_mode):
                min_html = tmp_text
                write_file(self.__tmp_file, tmp_text)
            else:
                print ('> BACK')

        self.__min_html = min_html 

    def __minimize_space(self):
        if isinstance(self.__min_html, list):
            self.__min_html = '\n'.join(self.__min_html)
        self.__min_html = re.sub(r'(\n\s*)+\n+', '\n\n', self.__min_html)
        self.__min_html = self.__min_html.replace('{ }', '')
        self.__min_html = self.__min_html.split('\n')

        tmp_html = self.__min_html
            
        for i, line in enumerate(self.__min_html):
            words = line.split(' ')
            num_words = len(words)

            trim_idx = 0
            for j in range(num_words):
                prev = self.__min_html[i]

                tmp_words = prev.split(' ')
                if 'id' in tmp_words[trim_idx]:
                    trim_idx += 1
                    continue
                del tmp_words[trim_idx]

                tmp_line = ' '.join(tmp_words)

                tmp_html[i] = tmp_line

                write_file(self.__trim_file, tmp_html)

                if self.__is_reproducible(self.__aggr_mode):
                    self.__min_html[i] = tmp_line
                    write_file(self.__tmp_file, tmp_html)
                    print ('> Current file size: {}'.format(os.path.getsize(self.__tmp_file)))
                else:
                    tmp_html[i] = prev
                    trim_idx += 1

    def __minimize_sline(self, idx, style_lines):
        style_line = style_lines[idx]

        style_line = re.sub('{ ', '{ \n', style_line)
        style_line = re.sub(' }', ' \n}', style_line)
        style_line = re.sub('; ', '; \n', style_line)
        style_blocks = style_line.split('\n')

        print('> Minimizing style idx: {} ...'.format(idx))
        print('> Initial style entries: {}'.format(len(style_blocks)))

        min_blocks = style_blocks
        min_indices = range(len(style_blocks))

        trim_sizes = [ pow(2,i) for i in range(3,-1,-1) ] # 8, 4, 2, 1
        trim_sizes = [x for x in trim_sizes if x < len(style_blocks)]
        for trim_size in trim_sizes:
            print('> Setting trim size: {}'.format(trim_size))
            for offset in range(1, len(style_blocks) - 2, trim_size):
                if offset not in min_indices:
                    continue
                print('> Current style entries: {}'.format(len(min_blocks)))

                trim_indices = range(offset, min(offset + trim_size, len(style_blocks) - 2))

                tmp_blocks = []
                tmp_indices = []
                for i, line in enumerate(style_blocks):
                    if i not in trim_indices and i in min_indices:
                        tmp_blocks.append(style_blocks[i])
                        tmp_indices.append(i)

                last_block =  tmp_blocks[-1]
                if last_block[-2:] == '; ':
                    tmp_blocks[-1] = last_block[:-2] + ' '

                tmp_line = ''.join(tmp_blocks) + '\n'

                style_lines[idx] = tmp_line

                tmp_html = re.sub(re.compile(r'<style>.*?</style>', re.DOTALL), \
                                  '<style>\n' + ''.join(style_lines) + '\n</style>', self.__cat_html)

                write_file(self.__trim_file, tmp_html)

                if self.__is_reproducible(self.__aggr_mode): #
                    min_blocks = tmp_blocks
                    min_indices = tmp_indices
                    write_file(self.__tmp_file, tmp_html)
                else:
                    continue

        min_line = ''.join(min_blocks) + '\n'
        return min_line

    def __minimize_slines(self, style):
        style_content = style.contents[0]
        style_lines = [ line + '\n' for line in style_content.split('\n') if '{ }' not in line]
        #print (style_lines)

        min_lines = style_lines
        for i in range(len(style_lines)):
            min_line = self.__minimize_sline(i, min_lines)
            min_lines[i] = min_line

        min_style = '<style>\n' + ''.join(min_lines) + '\n</style>'
        return min_style

    def __minimize_token(self):
        if isinstance(self.__min_html, list):
            self.__cat_html = '\n'.join(self.__min_html)
        else:
            self.__cat_html = self.__min_html

        soup = BeautifulSoup(self.__cat_html, "lxml")
        if soup.style is not None and soup.style != " None":
            try:
                min_style = self.__minimize_slines(soup.style)
                self.__cat_html = re.sub(re.compile(r'<style>.*?</style>', re.DOTALL), \
                                       min_style, self.__cat_html)

                self.__min_html = [ line + '\n' for line in self.__cat_html.split('\n') ]
            except:
                print ('style is ', soup.style, file=sys.stderr)
                return
        else:
            return True

    def __minimize_dom(self):
        br = self.__fuzzer.br_list[-1]
        br.run_html(self.__tmp_file)
        tree = br.get_all_trees()

        dom_tree = tree[DOM]
        
        for i in reversed(range(len(dom_tree))):
            state = self.__fuzzer.test_html(self.__tmp_file, 
                    'document.querySelectorAll(\'*\')[{}].remove();'
                    .format(i))

            if state is not None and state.bug_type != NON_BUG:
                write_file(self.__trim_file, br.get_source())
                state_ = self.__fuzzer.test_html(self.__trim_file) 
                if state_ is not None and state_.bug_type != NON_BUG:
                    print ('{} is removed'.format(dom_tree[i]))
                    self.__min_html = br.get_source()
                    write_file(self.__tmp_file, self.__min_html)

            state = self.__fuzzer.test_html(self.__tmp_file, 
                    'document.querySelectorAll(\'*\')[{}].textContent = \'\';'
                    .format(i))
            if state is not None and state.bug_type != NON_BUG:
                write_file(self.__trim_file, br.get_source())
                state_ = self.__fuzzer.test_html(self.__trim_file) 
                if state_ is not None and state_.bug_type != NON_BUG:
                    print ('text in {} is removed'.format(dom_tree[i]))
                    self.__min_html = br.get_source()
                    write_file(self.__tmp_file, self.__min_html)

    def __minimize_domnode(self):
        br = self.__fuzzer.br_list[-1]
        br.run_html(self.__tmp_file)
        tree = br.get_all_trees()

        dom_tree = tree[DOM]
        
        removed_num = 0
        idx = dom_tree.index('body')
        for i in range(len(dom_tree) - idx - 1):
            state = self.__fuzzer.test_html(self.__tmp_file,
                    'temp1 = document.body.querySelectorAll(\'*\')[{}];'.format(i - removed_num) + 
                    'if (temp1.nextElementSibling) {' +
                    'temp1.parentNode.append(...temp1.childNodes, temp1.nextElementSibling);}' +
                    'else { temp1.parentNode.append(...temp1.childNodes);} ' + 
                    'temp1.remove();'
                    )

            if state is not None and state.bug_type != NON_BUG:
                write_file(self.__trim_file, br.get_source())
                state_ = self.__fuzzer.test_html(self.__trim_file) 
                if state_ is not None and state_.bug_type != NON_BUG:
                    print ('{} is removed'.format(dom_tree[i]))
                    self.__min_html = br.get_source()
                    write_file(self.__tmp_file, self.__min_html)
                    removed_num += 1

    def __minimize_attr(self):
        br = self.__fuzzer.br_list[-1]
        br.run_html(self.__tmp_file)
        tree = br.get_all_trees()

        dom_tree = tree[DOM]
        attr_tree = tree[ATTRS]
        
        for i, tag in enumerate(dom_tree):
            for attr in attr_tree[i]: 
                state = self.__fuzzer.test_html(self.__tmp_file, 
                        'document.querySelectorAll(\'*\')[{}].removeAttribute(\'{}\');'
                        .format(i, attr))

                if state is not None and state.bug_type != NON_BUG:
                    write_file(self.__trim_file, br.get_source())
                    state_ = self.__fuzzer.test_html(self.__trim_file) 
                    if state_ is not None and state_.bug_type != NON_BUG:
                        self.__min_html = br.get_source()
                        print ('{} is removed'.format(attr))
                        write_file(self.__tmp_file, self.__min_html)

    def __minimize_style(self):
        br = self.__fuzzer.br_list[-1]
        br.run_html(self.__tmp_file)
        tree = br.get_all_trees()

        dom_tree = tree[DOM]
        for i, tag in enumerate(dom_tree):
            style_len = int(br.exec_script(
                    'sele = document.querySelectorAll(\'*\')[{}].style; return sele.length'
                    .format(i)))
            for j in reversed(range(style_len)):
                state = self.__fuzzer.test_html(self.__tmp_file, 
                        'sele = document.querySelectorAll(\'*\')[{}].style; sele.removeProperty(sele[{}]);'
                        .format(i,j))
                if state is not None and state.bug_type != NON_BUG:
                    write_file(self.__trim_file, br.get_source())
                    state_ = self.__fuzzer.test_html(self.__trim_file) 
                    if state_ is not None and state_.bug_type != NON_BUG:
                        self.__min_html = br.get_source()
                        print ('{}th style is removed'.format(j))
                        write_file(self.__tmp_file, self.__min_html)




    def __minimizing(self):
        self.__minimize_dom()
        self.__minimize_attr()
        self.__minimize_token()
        #self.__minimize_style()
        self.__minimize_line()
        self.__minimize_space()
        self.__minimize_domnode()
        self.__minimize_dom()

    def __is_reproducible(self, aggr=False):
        state_ = self.__fuzzer.test_html(self.__trim_file, self.__comms)
        if state_ is None: return False
        if not aggr:
            if self.__init_state.p_hashes[0] == state_.p_hashes[0]:
                if self.__init_state.p_hashes[1] == state_.p_hashes[1]:
                    return True
            return False
#            return state_ == self.__init_state
        else: 
            return state_.bug_type == BUG

    def run(self):

        prev_locs = None

        while True:
            queueLock.acquire()
            if not workQueue.empty():
                info = workQueue.get()
                br_locs = info[0]
                html_file = info[1]
                print (html_file)
            else:
                print ('Queue is Empty')
                queueLock.release()
                break
            queueLock.release()

            if prev_locs != br_locs:

                if self.__fuzzer is not None:
                    self.__fuzzer.terminate()
                    del self.__fuzzer

                self.__fuzzer = Cross_version(br_locs)
                prev_locs = br_locs

            if self.__get_file_for_trimming(html_file) is None:
                print ('Something wrong with ' + html_file)
                continue
            if self.__init_state is None: 
                print ('Init state is None with' + html_file)
                continue
            elif self.__init_state.bug_type == NON_BUG:
                print('{} is not a bug'.format(html_file))
                continue

            if size_limit and os.path.getsize(html_file) <= 1024:
                print('Smaller than 1024, pass {}'.format(html_file))
                continue

            copyfile_(html_file, self.__tmp_file)
            copyfile_(html_file, self.__trim_file)

            self.__minimizing()
            state = self.__fuzzer.test_html(self.__tmp_file)
            rmfile(self.__tmp_file)
            rmfile(self.__trim_file)
            if state is None or state.bug_type == NON_BUG:
                continue

            f_name = self.__html_file
            if not self.__overwrite:  f_name = f_name + '.html'

            data = re.sub(r'(\n\s*)+\n+', '\n\n', self.__fuzzer.br_list[0].get_source())
            write_file(f_name, data)
            #self.__fuzzer.test_html(f_name, save_shot=True)
            #print ('hi')

            queueLock.acquire()
            min_htmls[self.__html_file] = 1
            queueLock.release()


        self.__free_all()
            

if __name__ == '__main__':

    set_affinity(range(int(count_cpu() / 2)))
    set_signal()

    parser = argparse.ArgumentParser(description='Usage')
    parser.add_argument('-i', '--input', required=True, type=str, help='input directory')
    parser.add_argument('-o', '--output', required=False, type=str, help='input directory')
    parser.add_argument('-j', '--job', required=False, type=int, default=4, help='number of Threads')
    parser.add_argument('-b', '--browser', required=False, type=str, default='', help='browser config file')
    parser.add_argument('--meta', action="store_true", default=False, help='')
    parser.add_argument('--overwrite', action="store_true", default=False, help='')
    parser.add_argument('--aggr', action="store_true", default=False, help='')
    parser.add_argument('--size', action="store_true", default=False, help='')
    args = parser.parse_args()

    trimThreads = []

    size_limit = args.size

    display = virtual_display()
    display.start()

    if args.meta: mode = META
    else: mode = CROSS

    init_seeds = []

    if os.path.isdir(args.input) and os.path.exists(os.path.join(args.input, BR_PATHS)):
        tmp = get_all_files(args.input, E_HTML)
        xs = os.path.join(args.input, BR_PATHS)
        for f in tmp:
            init_seeds.append([xs, f])
    elif os.path.isfile(args.input):
        if args.browser == '': abort()
        init_seeds.append([args.browser, args.input])
    elif args.browser != "":
        tmp = get_all_files(args.input, E_HTML)
        for f in tmp:
            init_seeds.append([args.browser, f])
    else:
        abort()

    queueLock = threading.Lock()
    workQueue = Queue(len(init_seeds))

    min_htmls = {}

    for seed in init_seeds:
        min_htmls[seed[1]] = 0
        workQueue.put(seed)

    if args.output is not None:
        mkdir(args.output)

    num_proc = args.job
    if num_proc == 1:
        num_proc = min(len(init_seeds), 24)

    for idx in range(num_proc):
        mini = Minimizer(mode, args.overwrite, args.output, args.aggr) 
        trimThreads.append(mini)
        mini.start()
        sleep(3)

    for mini in trimThreads:
        mini.join()

    display.stop()

    for k in min_htmls:
        if min_htmls[k] == 0:
            print (k, ' is not minimized')
