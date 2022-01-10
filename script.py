#!/usr/bin/python3 -u
from src.config import *

def clean():
    os.system('pkill chrome')
    os.system('pkill Xvfb')

parser = argparse.ArgumentParser(description='Usage')
parser.add_argument('-i', '--input', required=True, type=str, help='input directory')
parser.add_argument('-o', '--output', required=True, type=str, help='output directory')
parser.add_argument('-m', '--mode', required=True, type=str, help='mode')

parser.add_argument('-r', '--ref', required=False, type=str, help='reference browser')
parser.add_argument('-b', '--browser', required=False, type=str, help='target browser')
args = parser.parse_args()

mode = args.mode
input_ = args.input
output = args.output

if mode == 'interoracle':
    for item in sorted(os.listdir(input_)):
        dir_ = os.path.join(input_, item)
        if os.path.isdir(dir_):
            cmd = 'python3 src/interoracle.py -i {} -o {} -r {}'.format(dir_, output, args.ref)
            print (cmd)
            process(cmd)
    clean()

elif mode == 'pipeline':
    for item in sorted(os.listdir(input_)):
        dir_ = os.path.join(input_, item)
        if os.path.isdir(dir_):
            cmd = 'python3 src/analyzer.py -i {} -o {}'.format(dir_, output)
            print (cmd)
            process(cmd)

elif mode == 'minimize':
    process('rm -rf {}'.format(output))
    process('cp -rf {} {}'.format(input_, output))
    for item in sorted(os.listdir(output)):
        dir_ = os.path.join(output, item)
        if os.path.isdir(dir_):
            cmd = 'python3 src/minimizer.py -i {} -j 1 --overwrite --aggr'.format(dir_)
            print (cmd)
            process(cmd)
    clean()

elif mode == 'fuzz':
    cmd = 'python3 src/r2z2.py -i {} -o {} -b {} -j 24'.format(input_, output, args.browser)
    print (cmd)
    process(cmd)
    clean()

elif mode == 'nonoracle':
    cmd = 'python3 src/nfuoracle.py -i {} -o {} -b {} -r {}'.format(input_, output, args.browser, args.ref)
    print (cmd)
    process(cmd)

elif mode == 'bisect':
    if output[-1] == '/':
        output = output[:-1]

    tmp_output = output + '_tmp'
    cmd = 'python3 -u src/bisector.py -i {} -o {} -j 1 -b {}'.format(input_, tmp_output, args.browser)
    print (cmd)
    process(cmd)
    clean()
    for item in sorted(os.listdir(tmp_output)):
        dir_ = os.path.join(tmp_output, item)
        if os.path.isdir(dir_):
            cmd = 'python3 -u src/bisector.py -i {} -o {} -j 1 --build'.format(dir_, output)
            print (cmd)
            os.system(cmd)
            clean()
            sleep(5)
    copyfile_(os.path.join(tmp_output, 'bisected_list.txt'), 
            os.path.join(output, 'bisected_list.txt'))
    rmdir(tmp_output)
else:
    print ('Please check the arguments')

