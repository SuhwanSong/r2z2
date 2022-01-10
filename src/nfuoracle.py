from config import *

def run_command(path, ref):
    cmd = './tools/wpt/wpt run --headless '
    cmd += '--binary {} '.format(path)

    if CHROME in path:
        cmd += '--webdriver-binary {} chrome {}'.format(
                path + 'driver', ref)
    else:
        cmd += '--webdriver-binary {} firefox {}'.format(
                os.path.dirname(path) + '/../geckodriver', ref)
#    print (cmd)
    status = process(cmd)

    return status.returncode
    

def analyze_commit(ref_browser, target_browser, pos):
    commit = get_chrome_commit_from_position(pos)
    src_dir = 'chrome/src'
    wpt_dir = os.path.join(src_dir, 'third_party/blink/web_tests')

    changed = '/tmp/diff_files'

    process('./tools/git_file_diff.sh {} {}'.format(commit, changed))
    files = read_file(changed)

    lists = []
    org_files = {}
    ref_files = {}
    for file_ in files:
        file_ = file_[8:-1]
        if 'crash' in file_ or 'ref' in file_: continue

        elif file_.endswith(E_HTML) or file_.endswith('.png') or file_.endswith('.txt'):
            org_files[file_] = 'HTML'
            bn = basename(file_.replace('-expected', '').replace('.png', E_HTML).replace('.txt', E_HTML))
            path = find(wpt_dir, bn)
            if not path: continue
#            print (path)
            ref_files[path] = 1

    fuzzer_dir = os.path.dirname(__file__)
    browser_dir = os.path.abspath(os.path.join(fuzzer_dir, os.pardir))
    commits = read_file('data/bisect-builds-cache.csv', 'str').split(', ')
    tmp_path = os.path.join(browser_dir, CHROME)


    for ref in ref_files:
        if 'external/wpt' in ref:
            ref = ref.split('external/wpt/')[-1]
            ref = ref.replace('\n', '')
            lists.append(ref)

    if not lists: return 1

    ref = ' '.join(lists)
#    print (ref)
    status_ch = run_command(target_browser, ref)
    status_fr = run_command(ref_browser, ref)

    if status_ch == 0 and status_fr == 1: return 0
    else: return 2

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Usage')
    parser.add_argument('-i', '--input', required=True, type=str, help='input directory')
    parser.add_argument('-o', '--output', required=True, type=str, help='output directory')
    parser.add_argument('-b', '--br', required=True, type=str, help='target browser path')
    parser.add_argument('-r', '--ref', required=True, type=str, help='reference browser path')
    args = parser.parse_args()

    target_browser = read_file(args.br)[-1].replace('\n', '')
    print (target_browser)

    rmdir(args.output)
    mkdir(args.output)

    bug_list = {}
    for dir_ in sorted(os.listdir(args.input)):
        intdir = int(dir_)
        result = analyze_commit(args.ref, target_browser, intdir)
        bug_list[intdir] = result
        if result > 0: # bug
            input_path = os.path.join(args.input, dir_)
            bugfiles = get_pathlist(input_path + '/*.html')
            poc_dir = os.path.join(args.output, dir_)
            mkdir(poc_dir)
            poc_path = os.path.join(poc_dir, 'PoC.html')
            copyfile_(random.choice(bugfiles), poc_path)
            copyfile_(os.path.join(input_path, BR_PATHS), os.path.join(poc_dir, BR_PATHS)) 

    for pos in sorted(bug_list.keys()):
        if bug_list[pos] == 1:
            print (pos, 'is a bug: no wpt')

        elif bug_list[pos] == 2:
            print (pos, 'is a bug')
        else:
            print (pos, 'is a not bug')
