from config import *
from selenium import webdriver
import pychrome

# Chrome option
WIDTH = 768
HEIGHT = 768
HEADLESS = '--headless'
DISABLE_SANDBOX = '--disable-seccomp-sandbox --no-sandbox'
DISABLE_LOGGING = '--disable-logging'
DISABLE_GPU = '--disable-gpu'
GPU_BENCH = '--enable-gpu-benchmarking'
REMOTE_PORT = '--remote-debugging-port='

# Common script
SCROLL_TO_0 = 'window.scrollTo(0, 0);' 

class Layer:
    LS = 'layers'
    LID = 'layerId'
    LPID = 'parentLayerId'
    BNID = 'backendNodeId'
    CPRS = 'compositingReasons'
    PC = 'paintCount'

class browser:
    def __init__(self, bin_path, use_port=False):

        self.port = None

        if not os.path.exists(bin_path): abort()
        self.version = get_parent_dirname(bin_path)
        
        if CHROME in bin_path:
            for i in range(8888, 65536):
                if not is_port_open(i):
                    self.port = i
                    break

            self.project = CHROME
            self.options = webdriver.chrome.options.Options()
            self.options.add_argument(DISABLE_SANDBOX)
            self.options.add_argument(DISABLE_LOGGING)
            self.options.add_argument(HEADLESS)
#            self.options.add_argument(DISABLE_GPU)
            self.options.add_argument(GPU_BENCH)
            if use_port:
                self.options.add_argument(REMOTE_PORT+str(self.port))
 
        elif FIREFOX in bin_path:
            self.project = FIREFOX
            self.options = webdriver.firefox.options.Options()
            self.options.add_argument(HEADLESS)
            self.options.add_argument(DISABLE_GPU)
        else: abort()

        self.options.binary_location = bin_path

        self.__num_of_run = 0

        num_try = 0
        self.browser = None
        while self.browser is None: 
            try:
                self.__set_browser()
            except Exception as e:
                print (e)
                if num_try == NUM_OF_ITER:
                    return

                num_try += 1
                print('{}th try to start Browser {}'.format(num_try, bin_path))

    def __set_browser(self):
        if is_chrome(self.project):
            self.browser = webdriver.Chrome(chrome_options=self.options,
                executable_path=self.options.binary_location + 'driver')
            self.browser.set_window_size(WIDTH, HEIGHT)
        elif is_firefox(self.project):
            self.browser = webdriver.Firefox(firefox_options=self.options,
                executable_path=os.path.dirname(self.options.binary_location) + '/../geckodriver')

            self.browser.set_window_size(WIDTH, HEIGHT)
            self.__set_viewport_size(WIDTH, HEIGHT)
#            self.browser.set_window_size(WIDTH, HEIGHT * 1.1244509516837482 // 1)

        self.browser.set_script_timeout(TIMEOUT)
        self.browser.set_page_load_timeout(TIMEOUT)
#        self.browser.implicitly_wait(TIMEOUT)

        print('> Browser {} starts with port {}'.format(self.version, self.port))
        
    def __set_viewport_size(self, width, height):
        window_size = self.browser.execute_script("""
        return [window.outerWidth - window.innerWidth + arguments[0],
          window.outerHeight - window.innerHeight + arguments[1]];
        """, width, height)
        self.browser.set_window_size(*window_size)

    def __get_window_position(self):
        top = self.exec_script('return window.scrollX')
        left = self.exec_script('return window.scrollY')
        return top, left

    def __scroll(self):
        cc = 0
        self.exec_script(SCROLL_TO_0)
        top, left = self.__get_window_position()
        if is_firefox(self.project): return True
        while top != 0 or left != 0:
            if cc > 3: return False
            cc += 1
            self.exec_script(SCROLL_TO_0)
            top, left = self.__get_window_position()
        return True

    def kill_browser(self):
        self.__num_of_run = 0
        if self.browser is None:
            pass
        elif self.browser.session_id is not None:
            print('> Browser {} terminated'.format(self.version))
            self.browser.quit()

    def run_html(self, html_file):
        self.__num_of_run += 1
        if self.__num_of_run == MAX_RUN:
            self.kill_browser()
            self.__set_browser()
        try:
            while len(self.browser.window_handles) > 1: self.browser.close()
            self.browser.get('file://' + os.path.abspath(html_file))
            return True
        except Exception as ex:
            print (self.version, ex)
            self.kill_browser()
            self.__set_browser()
            return False

    def run_js(self, comm):

        rets = []
        comms = []
        last_command = ''

        if isinstance(comm, list):
            comms.extend(comm)
        elif isinstance(comm, str):
            comms.append(comm)
        else: return

        try:
            for command in comms:
                last_command = command
                if "await" in command:
                    continue
                rets.append(self.exec_script(command))
                sleep(0.005)
            return rets
        except Exception as ex:
            print(last_command)
            mesg = str(ex)
            if "id" in mesg or "Timed" in mesg or "property" in mesg:
                pass
            else:
                self.kill_browser()
                self.__set_browser()
            return False

    def screenshot_and_hash(self, name=None):
        try:
            if name is None: 
                hash_v = get_phash(self.browser.get_screenshot_as_png())
            else:
                self.screenshot(name)
                hash_v = get_phash(name)
            return hash_v
        except Exception as e: 
            print('try-again: error in s & h :' + str(e))
        try:
            self.kill_browser()
            self.__set_browser()
            return
        except Exception as e:
            print(str(e))
            return 

    def screenshot(self, name): 
        if not self.__scroll(): return 
        self.browser.save_screenshot(name)

    def get_source(self):
        try: return self.browser.page_source
        except: return

    def exec_script(self, scr, arg=None):
        return self.browser.execute_script(scr, arg)


    def get_all_cssTexts(self):
        return self.exec_script(
                'var cssText = [];'+
                'try {' + 
                'var classes = document.styleSheets[0].cssRules;'+
                'for (var x = 0; x < classes.length; x++)'+
                '{cssText.push(classes[x].cssText);}} catch (e){}'+
                'return cssText;')

    def get_all_css_rules(self):
        return self.exec_script(
                'var cssText = [];'+
#                'if (document.styleSheets[0]) {' +
                'try {' +
                'var classes = document.styleSheets[0].cssRules;'+
                'for (var x = 0; x < classes.length; x++)'+
                '{var z = classes[x].style; var rule = {};' +
                'for (var j = 0; j < z.length; j++) {rule[z[j]] = z[z[j]]}; cssText.push(rule)' +
                '}} catch (error) {};'+ 
                ' var classes = document.querySelectorAll(\'*\');'+
                'for (var x = 0; x < classes.length; x++)'+
                '{var z = classes[x].style; var rule = {};' +
                'if (z.length) {' +
                'for (var j = 0; j < z.length; j++) {rule[z[j]] = z[z[j]]}; cssText.push(rule)' +
                '}};'+ 
                'return cssText;')

    def get_all_trees(self, attr=False):
        trees = {DOM: [], STYLE: [], LAYOUT: [], DEPTH: [], ATTRS: []}
        try:
            elements = self.browser.find_elements_by_xpath('.//*')
        except Exception as e:
            return trees

        for element in elements:
            style_ = self.exec_script(
                    'var items = {};'+
                    'var st = getComputedStyle(arguments[0]);'+
                    'var len = st.length;'+
                    'for (i = 0; i < len; i++)'+
                    '{items [st[i]] = st.getPropertyValue(st[i])};'+
                    'return items;', element)
            layout = self.exec_script(
                    'return arguments[0].getBoundingClientRect()', element)
            depth = self.exec_script(
                    'var depth = 0; el=arguments[0];'+
                    'while(null!==el.parentElement)' +
                    '{el = el.parentElement; depth++ };' +
                    'return depth;', element)


            attrs = {}
            if attr:
                for att in element.get_property('attributes'):
                    attrs[att['name']] =  att['value']

            trees[ATTRS].append(attrs)
            trees[DOM].append(element.tag_name)
            trees[STYLE].append(style_)
            trees[LAYOUT].append(layout)
            trees[DEPTH].append(depth)

        return trees

    def get_paint(self):
        pass
#        mkdir('./tmp/skPic_{}'.format(self.version))
#        self.exec_script('chrome.gpuBenchmarking.printToSkPicture(\'./tmp/skPic_{}\')'.format(self.version))

    def get_pairs(self):
        elements = self.browser.find_elements_by_xpath('.//*')
        tmp = []
        for element in elements:
            if element.tag_name in ['html', 'head', 'style']:
                continue
            item = self.exec_script(
                    'var items = [];'+
                    'var x = arguments[0];' +
                    'var s = x.children;' +
                    'for (var j = 0; j < s.length; j++)' +
                    '{items.push([x.tagName, s[j].tagName])}' +
                    'return items'
                    , element)
            if item:
                tmp.extend(item)
        return tmp

    def get_css_pairs(self):
        items = self.exec_script(
                ' var items = []; var rules = document.styleSheets[0].cssRules;' +
                ' for (var i = 0; i < rules.length; i++) { ' +
                ' var tmps = [];' +
                ' var alls = document.querySelectorAll(rules[i].selectorText);'+
                ' for (var j = 0; j < alls.length; j++) {'+
                ' if (!tmps.includes(alls[j])) {tmps.push(alls[j]);}' +
                ' var chils = alls[j].getElementsByTagName("*");' +
                ' for (var k = 0; k < chils.length; k++) { ' +
                '    if (!tmps.includes(chils[k])) { tmps.push(chils[k]); }} ' +
                ' items.push(tmps); }}' +
                ' return items;'
                )
        return items

    def request_layer(self, **kwargs):
        self.layers = kwargs

    def xxx(self, html_file):
        browser = pychrome.Browser(url="http://127.0.0.1:" +str(self.port))
        tab = browser.new_tab()

        tab.LayerTree.layerTreeDidChange = self.request_layer
        tab.start()
        tab.LayerTree.enable()
        tab.Page.navigate(url='file://' + os.path.abspath(html_file), _timeout=6)
        tab.wait(6)

        lcfg = Layer()
        layers = self.layers[lcfg.LS]
        ids = []
        paint_log = []
        images = []
        for layer in layers:
            id_ = layer[lcfg.LID]
            ids.append(id_)
            if layer[lcfg.PC] == 0:
                paint_log.append({})
                continue
            try:
                snapId = tab.LayerTree.makeSnapshot(layerId=layer[lcfg.LID])
                sleep(0.2)
                ret = tab.LayerTree.replaySnapshot(snapshotId=snapId['snapshotId'])['dataURL'][22:]
                images.append(ret)
                x = ret.encode('ascii')  
                import base64
                with open("imageToSave{}_{}.png".format(self.version, id_), "wb") as fh:
                    fh.write(base64.decodebytes(x))
                ret = tab.LayerTree.snapshotCommandLog(snapshotId=snapId['snapshotId'])
                paint_log.append(ret)
            except pychrome.exceptions.CallMethodException as e:
                paint_log.append({})
        compo_log = []
        for layer in layers:
            compo_log.append(
                    tab.LayerTree.compositingReasons(
                        layerId=layer[lcfg.LID]))
#        print ('ids: ', ids)
#        print (paint_log)
#        for layer in layers:
#            layer.pop(lcfg.LID, None)
#            layer.pop(lcfg.BNID, None)
#            layer.pop(lcfg.LPID, None)

        tab.stop()
        browser.close_tab(tab)
        return layers, paint_log, compo_log, images
