function set_background() {
    const color_map = ["red", "green", "blue", "yellow", "brown", "rgb(255, 255, 128);", "#74992e;", "hsla(50, 33%, 25%, .75);", "hsla(240, 33%, 25%, .75);"]
    var eles = get_elements();
    for (var i = 0; i < eles.length; i++) {
        eles[i].style.backgroundColor = color_map[i % color_map.length]
    }
}

function get_elements() {
    return document.body.querySelectorAll('*');
}

function get_id_elements() {
    return document.querySelectorAll('*[id]');
}

function traverse_DOM(el, depth, dom_tree) {
    dom_tree.push([el, depth]);
    for(var i=0; i<el.children.length; i++) {
        traverse_DOM(el.children[i], depth+1, dom_tree);
    }
}

function get_DOM_structure() {
    node = document.body
    var nodes = [];
    if (node != null) {
        var stack = [];
        stack.push(node);
        while (stack.length != 0) {
            var item = stack.pop();
            nodes.push(item.tagName);
            var children = item.children;
            for (var i = children.length - 1; i >= 0; i--)
                stack.push(children[i]);
        }
    }
    return nodes.join('\n')
}

function get_all_classes() {
    var allClasses = [];
    var allElements = get_elements();

    for (var i = 0; i < allElements.length; i++) {
        var classes = allElements[i].className.toString().split(/\s+/);
        for (var j = 0; j < classes.length; j++) {
            var cls = classes[j];
            if (cls && allClasses.indexOf(cls) === -1)
                allClasses.push(cls);
        }
    }
    return allClasses;
}

function get_all_tags() {
    var allTags = [];
    var allElements = get_elements();

    for (var i = 0; i < allElements.length; i++) {
        var name = allElements[i].tagName.toString();
        if (name && allTags.indexOf(name) === -1)
            allTags.push(name);
    }
    return allTags;
}

function get_all_ids() {
    var allIds = [];
    var allElements = get_elements();

    for (var i = 0; i < allElements.length; i++) {
        var name = allElements[i].id.toString();
        if (name && allIds.indexOf(name) === -1)
            allIds.push(name);
    }
    return allIds;
}

function get_css_rules() {

    var css_rules = document.styleSheets[0].cssRules
    var css_r = []

    for (var i = 0; i < css_rules.length; i++) {
        var rr = css_rules[i]
        css_r.push(rr.selectorText+' {' + rr.style.cssText)
    }

    return css_r.join('\n')

}

function get_all_computed_styles() {

    const tab = '  ';

    var r = [];
    var eles = [];
    traverse_DOM(document.body, 0, eles)

    for (var i = 0; i < eles.length; i++) {
        const tmp = eles[i]
        const st = getComputedStyle(tmp[0])
        r.push(tab.repeat(tmp[1]) + '<' + tmp[0].tagName.toLowerCase() + '>:;' + st.cssText)
    }
    return r.join('\n')
}

function get_all_layout() {

    const tab = '  ';

    var r = [];
    var eles = [];
    traverse_DOM(document.body, 0, eles)
    
    for (var i = 0; i < eles.length; i++) {
        const tmp = eles[i]
        var info = ''
        var rect = tmp[0].getBoundingClientRect();
        info = tab.repeat(tmp[1]) + '<' + tmp[0].tagName.toLowerCase() + '>:;'  
            +  'bottom: ' + rect.bottom + '; '
            +  'height: ' + rect.height + '; '
            +  'left: '   + rect.left   + '; '
            +  'right: '  + rect.right  + '; '
            +  'top: '    + rect.top    + '; '
            +  'width: '  + rect.width  + '; '
            +  'x: '      + rect.x      + '; '
            +  'y: '      + rect.y      + '; '

        r.push(info)
    }
    return r.join('\n')
}

//function get_all_computed_styles() {
//    var eles = get_elements();
//    var r = [];
//    for (var i = 0; i < eles.length; i++) {
//        const st = getComputedStyle(eles[i])
//        if (st.display === 'none') { 
//            continue;
//        }
//
//        r.push(eles[i].tagName + ':;' + st.cssText)
//    }
//    return r.join('\n')
//}
//
//function get_all_layout() {
//    var eles = get_elements();
//    var r = [];
//    
//    for (var i = 0; i < eles.length; i++) {
//        var info = ''
//        var rect = eles[i].getBoundingClientRect();
//        info = eles[i].tagName + ':;' +  
//            + 'bottom: ' + rect.bottom + '; '
//            +  'height: ' + rect.height + '; '
//            +  'left: '   + rect.left   + '; '
//            +  'right: '  + rect.right  + '; '
//            +  'top: '    + rect.top    + '; '
//            +  'width: '  + rect.width  + '; '
//            +  'x: '      + rect.x      + '; '
//            +  'y: '      + rect.y      + '; '
//
//        r.push(info)
//    }
//    return r.join('\n')
//}


/* rendering checker */
function save_all_states() {
    window.prev_dom_state = document.body.cloneNode(true)
    window.prev_css_state = get_css_rules()
    window.prev_rt_state = get_all_computed_styles();
}

function is_dom_same() {
    if (!window.prev_dom_state.isEqualNode(document.body)) {
        return false
    }

    return get_css_rules() == window.prev_css_state
}

function is_rt_same() {
    return get_all_computed_styles() == window.prev_rt_state
}


function html_to_element(html) {
    var template = document.createElement('template');
    html = html.trim(); 
    template.innerHTML = html;
    return template.content.firstChild;
}

function tag_change(idx, tag){
    var eles = get_elements();
    const len = eles.length;

    if (len < 1) return ;

    var orl = eles[idx % len];
    var rep = document.createElement(tag);
    for(var i = 0, l = orl.attributes.length; i < l; ++i){
        var nName  = orl.attributes.item(i).nodeName;
        var nValue = orl.attributes.item(i).nodeValue;
        rep.setAttribute(nName, nValue);
    }
    rep.innerHTML = orl.innerHTML;
    orl.parentNode.replaceChild(rep, orl);
}

function add_element(idx, pos, html) {  // DONE
    var eles = get_elements();
    var llen = eles.length;
    
    if (llen > 0) {
        var ele = eles[idx % llen]
        window.new_element = html_to_element(html)
        ele.insertAdjacentElement(pos, window.new_element);
        window.pass = false
    } else {
        window.pass = true
    }
}

function add_element_restore() {  // DONE
    if (window.pass) {return }
    window.new_element.remove()
}

function del_element(idx) {             // DONE
    var eles = get_elements(); 
    const len = eles.length;
    if (len > 0) {
        eles[idx % len].remove();
    }
}

function del_element_meta(idx){         // DONE
    var eles = get_elements();
    const len = eles.length;

    if (len == 0) {
        window.pass = true
        return
    } else {
        window.pass = false
    }

    var ele = eles[idx % len];
    window.ele = ele

    var prev = ele.previousElementSibling;
    var next = ele.nextElementSibling;
    var pare = ele.parentElement;

//    if (prev && prev == ele.previousSibling) { window.cur = prev; window.pos = 1 } 
//    else if (next && next == ele.nextSibling) { window.cur = next; window.pos = 2 } 
    if (prev) { window.cur = prev; window.pos = 1 } 
    else if (next) { window.cur = next; window.pos = 2 } 
    else if (pare) { window.cur = pare; window.pos = 3 }

    ele.remove()
}

function del_element_restore() {        // DONE
    if (window.pass) {return }
    if (window.pos == 1) { window.cur.insertAdjacentElement('afterend', window.ele)  }
    else if (window.pos == 2) { window.cur.insertAdjacentElement('beforebegin', window.ele)  }
    else if (window.pos == 3) { window.cur.insertAdjacentElement('afterbegin', window.ele)  }
}

function add_attribute(idx1, attr, val) { // DONE
    var eles = get_elements()

    if (eles.length == 0) {
        window.pass = true
        return ;
    } else {
        window.pass = false
    }

    var ele = eles[idx1 % eles.length]
    window.ele = ele
    window.attr_name = attr
    window.attr_val = ele.getAttribute(attr)
    ele.setAttribute(attr, val)
}

function add_attribute_restore() { // DONE
    if (window.pass) { return }

    if (window.attr_val) {
        ele.setAttribute(window.attr_name, window.attr_val)
    } else {
        ele.removeAttribute(window.attr_name)
    }

}

function del_attribute(idx1, idx2) {   // DONE

    var eles = get_elements()

    if (eles.length == 0) {
        window.pass = true
        return ;
    } else {
        window.pass = false
    }

    var ele = eles[idx1 % eles.length]
    window.ele = ele
    var y = ele.getAttributeNames()

    if (y.length == 0) {
        window.pass = true
        return ;
    } else {
        window.pass = false
    }

    window.attr_name = y[idx2 % y.length] 
    window.attr_val = ele.getAttribute(window.attr_name)
    ele.removeAttribute(window.attr_name)
}

function del_attribute_restore() {     // DONE
    if (window.pass) { return }
    window.ele.setAttribute(window.attr_name, window.attr_val)
}

function add_css(type, idx, css) {  // DONE
    var prep = ''
    var selector = ''
    var selectors = []
    if (type == 'id') {
        selectors = get_all_ids(); 
        prep = '#'
    } else if (type == 'class') {
        selectors = get_all_classes();
        prep = '.'
    } else if (type == 'tag') {
        selectors = get_all_tags();
    } else {
        selectors = ['*']
    }

    const len_sel = selectors.length

    if (len_sel == 0) {
        prep = ''
        selector = '*'
    } else {
        selector = selectors[idx % len_sel]
    }

    window.sheet_f = document.styleSheets[0]
    var sheet_f = window.sheet_f

    const llen = sheet_f.rules.length - 1
    if (llen == -1) { 
        window.rule_pos = 0
    } else {
        window.rule_pos = llen
    }
    window.css_f = prep + selector + css
    sheet_f.insertRule(window.css_f, llen)
}

function add_css_restore() {  // DONE
    window.sheet_f.removeRule(window.rule_pos)
}

function del_css(idx) {   // DONE
    window.sheet_f = document.styleSheets[0]
    var sheet_f = window.sheet_f

    const llen = sheet_f.rules.length
    if (llen < 2) {
        window.pass = true
        return
    } else {
        window.pass = false
    }
    window.rule_pos = idx % (llen - 1)
    var rule_pos = window.rule_pos

    window.css_f = sheet_f.rules[rule_pos].cssText
    sheet_f.removeRule(rule_pos)
}

function del_css_restore() { // DONE
    if (!window.pass) {
        window.sheet_f.insertRule(window.css_f, window.rule_pos)
    }
}


// Functions below are not suitable for metamorphic testing
function add_css_property(idx, prop, val) {
    // TODO
    window.sheet_f = document.styleSheets[0]
    var sheet_f = window.sheet_f

    const llen = sheet_f.rules.length
    if (llen < 2) {
        window.pass = true
        return
    } else {
        window.pass = false
    }
    const rule_pos = idx % (llen - 1)

    window.c_style = sheet_f.rules[rule_pos].style
    var style = window.c_style

    window.prev_val = style.getPropertyValue(prop)
    style.setProperty(prop, val)
    window.prop = prop

}

function add_css_property_restore() {
    // TODO
    if (window.pass) {return }
    if (window.prev_val) {
        window.c_style.setProperty(window.prop, window.prev_val)
    } else {
        window.c_style.removeProperty(window.prop)
    }
}

function del_css_property(idx1, idx2) { // DONE
    var sheet_f = document.styleSheets[0]
    const llen = sheet_f.rules.length
    if (llen < 2) {
        window.pass = true
        return
    } else {
        window.pass = false
    }
    const rule_pos = idx1 % (llen - 1)

    window.c_style = sheet_f.rules[rule_pos].style
    var style = window.c_style
    var rlen = style.length

    if (rlen == 0) {
        window.pass = true
        return
    } else {
        window.pass = false
    }

    window.prop = style[idx2 % rlen]  
    var prop = window.prop
    window.prop_val = style.getPropertyValue(prop)
    style.removeProperty(prop)
}

function del_css_property_restore() { // DONE
    if (window.pass) {return }
    window.c_style.setProperty(window.prop, window.prop_val)
}


function def(){
    document.body.click(); 
}
