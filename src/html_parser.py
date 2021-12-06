import os
import copy
import random
from bs4 import BeautifulSoup
from config import read_file, META, CROSS, rand 
from domato.generator import setup_for_html_generation, gen_html, gen_css


class Html_parser:
    def __init__(self, html):
        self.html = html
        self.tree = None
        self.subtree = []
        self.attrs = {}

    def parse(self):
        soup = BeautifulSoup(self.html, "html.parser")
        self.tree = soup.body
#        self.subtree.append(soup.body)
        self.travel(soup.body)

    def prettify(self):
        soup = BeautifulSoup(self.html, "html.parser")
        return soup.prettify() 

    def set_html(self, html):
        self.html = html
        self.parse()

    def travel(self, soup):
        for child in soup.children:
            try:
                self.attrs.update(child.attrs)                
                self.subtree.append(child)
                self.travel(child)
            except:
                None

    def length(self):
        return len(self.subtree)

    def append(self, src_idx, dst_idx):
        tmp_tree = copy.copy(self.tree)
        tmp_subtree = copy.copy(self.subtree)

        self.subtree[dst_idx].append(copy.copy(self.subtree[src_idx]))
        html = str(self.tree)
        self.tree = tmp_tree
        self.subtree = tmp_subtree
        return html

    def insert_before(self, src_idx, dst_idx):
        tmp_tree = copy.copy(self.tree)
        tmp_subtree = copy.copy(self.subtree)

        self.subtree[dst_idx].insert_before(copy.copy(self.subtree[src_idx]))
        html = str(self.tree)
        self.tree = tmp_tree
        self.subtree = tmp_subtree
        return html

    def insert_after(self, src_idx, dst_idx):
        tmp_tree = copy.copy(self.tree)
        tmp_subtree = copy.copy(self.subtree)

        self.subtree[dst_idx].insert_after(copy.copy(self.subtree[src_idx]))
        html = str(self.tree)
        self.tree = tmp_tree
        self.subtree = tmp_subtree
        return html

    def delete(self, idx):
        tmp_tree = copy.copy(self.tree)
        tmp_subtree = copy.copy(self.subtree)

        self.subtree[idx].decompose()
        html = str(self.tree)
        self.tree = tmp_tree
        self.subtree = tmp_subtree
        return html

    def replace(self, src_idx, dst_idx):
        tmp_tree = copy.copy(self.tree)
        tmp_subtree = copy.copy(self.subtree)

        self.subtree[dst_idx].replace_with(copy.copy(self.subtree[src_idx]))
        html = str(self.tree)
        self.tree = tmp_tree
        self.subtree = tmp_subtree
        return html

    def swap(self, a_idx, b_idx):
        tmp_tree = copy.copy(self.tree)
        tmp_subtree = copy.copy(self.subtree)

        tmp = copy.copy(self.subtree[a_idx])
        self.subtree[a_idx].replace_with(copy.copy(self.subtree[b_idx]))
        self.subtree[b_idx].replace_with(copy.copy(tmp))
        html = str(self.tree)
        self.tree = tmp_tree
        self.subtree = tmp_subtree
        return html

class DOMAPI:
    def __init__(self, mode):

        self.htmlgrammar, self.cssgrammar = setup_for_html_generation()

        html = gen_html(self.htmlgrammar)
        self.html_parser = Html_parser(html)
        self.html_parser.parse()

        self.tags = []
        self.max_index = 200
        self.num_of_used_html = 0
        self.thre_to_gen = 16

        self.__mode = mode

        tags = read_file('./data/html_tags')
        for tag in tags:
            self.tags.append(tag[1:-2])

        self.__generate_css()

        if self.__mode == META:
            self.__weight_metamorphic_primitives()

    def generate_scripts(self):
        if self.__mode == CROSS:
            return self.apis_for_diff()
        elif self.__mode == META:
            return self.apis_for_meta()


    def __weight_metamorphic_primitives(self):
        self.func_list = []
        
        low_weight_list = [
            self.add_element_meta,
            self.add_css_meta,
            self.add_attribute_meta,     
            self.tag_meta,
        ]
        
        medium_weight_list = [
            self.remove_css_property_meta,  # CSS
            self.remove_attribute_meta,
        ]
        
        high_weight_list = [
            self.remove_element_meta,
            self.remove_css_meta,
        ]

        self.func_list.extend(low_weight_list * 1)
        self.func_list.extend(medium_weight_list * 2)
        self.func_list.extend(high_weight_list * 3)


    def __gen_and_set_html(self):
        self.num_of_used_html = 0
        self.html_parser.set_html(gen_html(self.htmlgrammar))

    def __generate_css(self):
        self.css_list = []
        self.num_of_used_css = 0

        css = gen_css(self.cssgrammar)
        tmp = css.split('\n')
        for line in tmp:
            string = line.split('{')
            if len(string) == 2:
                self.css_list.append('{' + string[1])

    def clean_html(self, string):
        return string.replace('\\','').replace('`','').replace('{','').replace('}', '')

    def __generate_apis_for_cross(self, num_range, func):
        comms = []
        num = rand(num_range)

        for i in range(num):
            idx = rand(self.max_index)
            comms.append(func(idx))
        return comms
        

    def apis_for_diff(self):
        num_range = 6
        comms = []

        comms.extend(self.__generate_apis_for_cross(
                    num_range, self.remove_element_diff))


#        num = rand(num_range)
#        for i in range(num): 
#            idx = rand(self.max_index) 
#            comms.append(self.remove_element_diff(idx))
        


        num = rand(num_range)
        for i in range(num):
            idx = rand(self.max_index) 
            comms.append(self.tag_diff(idx))

        num = rand(num_range)
        for i in range(num):
            idx = rand(self.max_index) 
            comms.append(self.remove_attribute_diff(idx))

        num = rand(10)
        if (num < 3):
            if self.num_of_used_html == self.thre_to_gen:
                self.__gen_and_set_html()
            idx = rand(self.max_index) 
            html = self.clean_html(str(random.choice(self.html_parser.subtree)))
            comms.append(self.add_element_diff(idx, html))
            self.num_of_used_html += 1

        if rand(1) == 0:
            random.shuffle(comms)

        return comms 


    def tag_diff(self, idx):
        return 'tag_change({},\'{}\'); '.format(idx, random.choice(self.tags))

    def remove_element_diff(self, idx):
        return 'del_element({});'.format(idx)

    def add_element_diff(self, idx, html): 
        pos_list = ['afterend', 'beforebegin', 'afterbegin']
        return 'add_element({},\'{}\',`{}`);'.format(idx, random.choice(pos_list), html)

    def remove_attribute_diff(self, idx):
        idx2 = rand(self.max_index) 
        return 'del_attribute({}, {});'.format(idx, idx2)

    def add_css_diff(self, idx, css):
        pass

    def remove_css_diff(self, idx):
        pass

    '''
    Metamorphic Testing

    '''

    def apis_for_meta(self):
        comms = []

        num = rand(1, 2 + 1)
        
        for i in range(num):
            comms.extend(random.choice(self.func_list)())

        return comms

    def add_element_meta(self): 
        comms = []
        idx = rand(self.max_index) 
        pos_list = ['afterend', 'beforebegin', 'afterbegin']

        if self.num_of_used_html == self.thre_to_gen:
            self.__gen_and_set_html()

        tmp = str(random.choice(self.html_parser.subtree))
        selected_html = self.clean_html(tmp)
        self.num_of_used_html += 1

        comms.append('add_element({},\'{}\',`{}`);'.format(idx, random.choice(pos_list), selected_html))

        comms.append('add_element_restore(); ')

        return comms

    def add_attribute_meta(self):
        comms = []
        idx = rand(self.max_index)

        if self.num_of_used_html == self.thre_to_gen:
            self.__gen_and_set_html()

        self.num_of_used_html += 1

        key = random.choice(list(self.html_parser.attrs))
        value = self.html_parser.attrs[key]
        
        comms.append('add_attribute({}, \'{}\', `{}`)'.format(idx, key, value))
        comms.append('add_attribute_restore(); ')

        return comms

    def add_css_meta(self):
        comms = []
        idx = rand(self.max_index) 
        selector_list = ['id', 'class', 'tag', 'other']

        if self.num_of_used_css == self.thre_to_gen:
            self.__generate_css()
        self.num_of_used_css += 1

        comms.append('add_css(\'{}\', {}, `{}`);'.format(
                    random.choice(selector_list), 
                    idx, 
                    random.choice(self.css_list)))

        comms.append('add_css_restore(); ')

        return comms


    def add_css_property_meta(self):
        pass


    def tag_meta(self):
        comms = []

        idx = rand(self.max_index) 

        comms.append('window.llen = get_elements().length; ') 
        comms.append('window.nameX = get_elements()[{} % window.llen].tagName; '.format(idx))
        comms.append('tag_change({},\'{}\'); '.format(idx,random.choice(self.tags)))
        comms.append('tag_change({}, window.nameX); '.format(idx))
        return comms

    def remove_element_meta(self):

        comms = []
        idx = rand(self.max_index) 

        comms.append('del_element_meta({}); '.format(idx))
        comms.append('del_element_restore(); ')

        return comms

    def remove_attribute_meta(self):
        comms = []
        idx1 = rand(self.max_index)
        idx2 = rand(self.max_index)

        comms.append('del_attribute({}, {}); '.format(idx1, idx2))
        comms.append('del_attribute_restore(); ')

        return comms

    def remove_css_meta(self):
        comms = []
        idx = rand(self.max_index)
        comms.append('del_css({}); '.format(idx))
        comms.append('del_css_restore(); ')
        return comms

    def remove_css_property_meta(self):
        comms = []
        idx1 = rand(self.max_index)
        idx2 = rand(self.max_index)

        comms.append('del_css_property({}, {}); '.format(idx1, idx2))
        comms.append('del_css_property_restore(); ')

        return comms


