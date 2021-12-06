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
    print (cmd)
    status = process(cmd)

    print (status.returncode)
    return status.returncode
    

def analyze_commit(ff, pos):
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
            print (file_)
            org_files[file_] = 'Expectation'
            changed = '/tmp/diff_file_test'

            process('./tools/git_content_diff.sh {} {}'.format(file_, changed))
            diffs = read_file(changed)

            for line in diffs:
                if '+++' in line or '---' in line or '+#' in line:
                    continue
                if 'external/wpt/' in line and line[0] == '-' or line[0] == '+':
                    line = line.split('external/wpt/')[-1].split(' [')[0].replace('\n','')
                    print (line)
                    lists.append(line)

    fuzzer_dir = os.path.dirname(__file__)
    browser_dir = os.path.abspath(os.path.join(fuzzer_dir, os.pardir))
    commits = read_file('data/bisect-builds-cache.csv', 'str').split(', ')
    tmp_path = os.path.join(browser_dir, CHROME)

    down_ver = pos

#    while not str(down_ver) in commits:
#        down_ver += 1
#    print (down_ver)

#    down_ver = 904231  
    down_ver = 784051

    for ref in ref_files:
        if 'external/wpt' in ref:
            ref = ref.split('external/wpt/')[-1]
            ref = ref.replace('\n', '')
            lists.append(ref)

    if not lists:
        return 1


    ch_path = os.path.join(tmp_path, str(down_ver), CHROME)
    download_browser(ch_path)

    ref = ' '.join(lists)
    print (ref)
    status_ch = run_command(ch_path, ref)
    status_fr = run_command(ff, ref)

#    if status_ch == 0 and status_ch == status_fr:
#        pass
    if status_ch == 0 and status_fr == 1:
        return 0
#    elif status_ch == 1 and status_fr == 1:
#        pass
    return 2
#
#    for ref in ref_files:
#        if 'external/wpt' in ref:
#            ch_path = os.path.join(tmp_path, str(down_ver), CHROME)
#            download_browser(ch_path)
#
#            ref = ref.split('external/wpt/')[-1]
#            print (ref)
#            status_ch = run_command(ch_path, ref)
#            status_fr = run_command(ff, ref)
#
#            if status_ch == 0 and status_ch == status_fr:
#                pass
#            elif status_ch == 0 and status_fr == 1:
#                return False
#            elif status_ch == 1 and status_fr == 1:
#                pass
#    return True                



if __name__ == '__main__':

#    set_affinity(range(int(count_cpu() / 2)))
#    set_signal()

    parser = argparse.ArgumentParser(description='Usage')
    parser.add_argument('-r', '--ref', required=True, default='', type=str, help='reference browser path')
    parser.add_argument('-p', '--ffpe', required=True, default=0, type=int, help='ffpe')
    args = parser.parse_args()

    bug_list = {}
    result = analyze_commit(args.ref, args.ffpe)
    if result == 1:
        with open('ffpe_result.txt', "a") as fp:
            fp.write('NO_WPT: {} by FFPE\n'.format(args.ffpe))
    elif result == 2:
        with open('ffpe_result.txt', "a") as fp:
            fp.write('REALBUG: {} by FFPE\n'.format(args.ffpe))
    else:
        with open('ffpe_result.txt', "a") as fp:
            fp.write('NOTBUG: {} by FFPE\n'.format(args.ffpe))
