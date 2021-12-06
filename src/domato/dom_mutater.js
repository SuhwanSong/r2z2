function get_elements() {
    return document.querySelectorAll('*[id]');
}
function get_all_elements() {
    return document.body.querySelectorAll('*');
}
function get_all_classes() {
    var allClasses = [];

    var allElements = document.querySelectorAll('*');

for (var i = 0; i < allElements.length; i++) {
  var classes = allElements[i].className.toString().split(/\s+/);
  for (var j = 0; j < classes.length; j++) {
    var cls = classes[j];
    if (cls && allClasses.indexOf(cls) === -1)
      allClasses.push(cls);
  }
}
}

function tag_change(idx, tag){
    var eles = get_elements();
    var len = eles.length;

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

function add_element(idx, pos, html) {
    var eles = get_elements();
    var len = eles.length;
    if (len > 0) {
        eles[idx % len].insertAdjacentHTML(pos, html);
    }
}

function del_element(idx) {
    var eles = get_elements();
    var len = eles.length;
    if (len > 0) {
        eles[idx % len].remove();
    }
}

function del_element_meta(idx){
    var eles = get_elements();
    var len = eles.length;
    ele = eles[idx % len];

    pos = 0
    var prev = ele.previousElementSibling;
    var next = ele.nextElementSibling;
    var pare = ele.parentNode;

    if (prev && prev == ele.previousSibling) { cur = prev; pos = 1 } 
    else if (next && next == ele.nextSibling) { cur = next; pos = 2 } 
    else if (pare) { cur = pare; pos = 3 }
    ele.remove()
}

function del_element_restore() {
    if (pos == 1) { cur.insertAdjacentHTML('afterend', ele.outerHTML)  }
    else if (pos == 2) { cur.insertAdjacentHTML('beforebegin', ele.outerHTML)  }
    else if (pos == 3) { cur.insertAdjacentHTML('afterbegin', ele.outerHTML)  }
}

function del_attribute(idx1, idx2) {
    var eles = get_elements()
    ele = eles[idx1 % eles.length]
    if (!ele) return ;
    var y = ele.getAttributeNames()

    attr_name = y[idx2 % y.length] 
    attr_val = ele.getAttribute(attr_name)
    ele.removeAttribute(attr_name)
}

function del_attribute_restore() {
    ele.setAttribute(attr_name, attr_val)
}


function def(){
    document.body.click(); 
}
