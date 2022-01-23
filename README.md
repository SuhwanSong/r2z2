 # R2Z2: Detecting Rendering Regressions in Web Browsers through Differential Fuzz Testing
 
 Repository for ["R2Z2: Detecting Rendering Regressions in Web Browsers through Differential Fuzz Testing"]() in ICSE'22. 

 
## Table
1. [Environment](#Environment)
2. [Setup](#Setup)
3. [Usage](#Usage)
4. [Reproduction](#Reproduction)
5. [Publication](#Publication)

## Environment
- Ubuntu 18.04 64bit
- 64+GB RAM
- 5TB+ Storage

## Setup
- You need to install the dependencies of R2Z2, and then download target browsers and reference browser with their drivers. 
- Each driver should be placed in the same directory of browser binary.
- The bash file `setup.sh` will install all of dependencies and download the browsers.
```shell
$ git clone https://github.com/SuhwanSong/r2z2.git
$ cd r2z2
$ ./setup.sh 
``` 

## Usage
You can easily run R2Z2 using `scripy.py`. The explanation of options is as follows. 
```
# Options
#   -i: input directory
#   -o: output directory
#   -b: file containing target browser paths
#   -r: reference browser path
#   -m: mode
```

####  0. Seed Generation
- You need to generate the html files for the test. 
- Please refer to [domato fuzzer](https://github.com/googleprojectzero/domato) to generate them.

####  1. Change Detector 
- The change detector finds the candidate html bugs from the seeds.
- You should provide the paths of target browser to the "browser_pathfile".
```shell
# Example
$ cat browser_pathfile
./chrome/766000/chrome
./chrome/784091/chrome
```
- After that, you can run the change detector using following command.
```
$ ./script.py -i [seed_dir] -o [candidate_output_dir] -b [browser_pathfile] -m fuzz
```

#### 2. Bisect Analysis
- The bisect analyzer pin-points the culprit commit of each candidate html bug.
- As you need to download and build many versions of chrome browser, it will take a lot of time.
```
$ ulimit -n 131072    # prevent too many open files
$ ./script.py -i [candidate_output_dir] -o [bisect_output_dir] -b [browser_pathfile] -m bisect
```

#### 3. Minimizer
- The minimizer minimizes the size of candidate html bugs.
```
$ ./script.py -i [bisect_output_dir] -o [minimize_output_dir] -m minimize
```

#### 4. Interoperability Oracle
- The interoperability oracle leverages the reference browser to discover oracle bugs from the candidate bugs.
```
$ ./script.py -i [minimize_output_dir] -o [inter_oracle_output_dir] -r [ref_browser_path] -m interoracle
```

#### 5. Non-feature-update Oracle
- The non-feature-update oracle leverages web-platform-tests to filter out the false positives from oracle bugs. 
```
$ cd tools/wpt
$ ./wpt make-hosts-file | sudo tee -a /etc/hosts
$ cd ../../
$ ./script.py -i [inter_oracle_output_dir] -o [oracle_output_dir] -b [browser_pathfile] -r [ref_browser_path] -m nonoracle
```

#### 6. Rendering Pipeline Analysis
- The rendering pipeline analysis identifies the culprit stage of oracle bug and provides the diff information.
```
$ ./script.py -i [oracle_output_dir] -o [analysis_output_dir] -m pipeline
```

## Reproduction

- All dataset used in paper is published at this [link](https://doi.org/10.6084/m9.figshare.16569561.v1). 
- Please download and extract it if you want to reproduce the result of paper.
- The initial seeds used in paper are located in `r2z2_data/seeds`.

### 6.1 Effectiveness of Change Detection
- To reproduce the result of test environment 1, please run the commands below.
- For test environment 2, please change "testenv1" to "testenv2" in the commands and run them.
```shell
$ mkdir eval_result_testenv1
$ ./script.py -i ./r2z2_data/seeds/testenv1 -o ./eval_result_testenv1/6.1 -b testenv1.txt -m fuzz
```

- The directory `./r2z2_data/seeds/testenv1` has 200K HTML inputs used in the paper.
- The directory `./eval_result_testenv1/6.1` includes the candidate html files found by R2Z2, e.g., `thread-00/id:000000_BUG.html`
- It also includes `fuzz_log.txt` file, which recorded the number of tested HTML files and candidate html files over the time during fuzzing.
- To check the result, please run the following command.
```shell
# It found 6785 candidates from 200K inputs for 6306 seconds.
$ cat ./eval_result_testenv1/6.1/fuzz_log.txt
Time(s), Tested HTMLs, CandBug
0.010046958923339844, 0, 0

...

6306.686718702316, 199998, 6785
```

### 6.2 Effectiveness of Bisect Analysis
- To reproduce the result of test environment 1, please run the commands below.
- For test environment 2, please change "testenv1" to "testenv2" in the commands and run them.
```
$ ./script.py -i ./eval_result_testenv1/6.1 -o ./eval_result_testenv1/6.2 -b testenv1.txt -m bisect
```
- The directory `./eval_result_testenv1/6.2` includes the successfully bisected candidate html files. 
- They are classified by their culprit commit (i.e., `B*`).  
- The `bisected_list.txt` file shows the list of the successfully bisected candidate html files.
- The `commit_info.txt` file is in each culprit commit directory, and it indicates the two different versions of browser (i.e., `A*` and `B*`)
- To check the number of bisected candidate html files, please run the following command. 
```shell
$ cat ./eval_result_testenv1/6.2/bisected_list.txt | wc -l
6643
```


### 6.3 Effectiveness of Regression Oracle
- To reproduce the result of test environment 1, please run the commands below.
- For test environment 2, please change "testenv1" to "testenv2" in the commands and run them.
```shell
# Minimizer
$ ./script.py -i ./eval_result_testenv1/6.2 -o ./eval_result_testenv1/6.2_min -m minimize

# Interoperability oracle
$ ./script.py -i ./eval_result_testenv1/6.2_min -o ./eval_result_testenv1/6.3_interoracle -r ./firefox/82.0/firefox -m interoracle

# Non-feature-update Oracle
$ cd tools/wpt
$ git checkout 412f681a0f62370130197d9b6311ee8ad34ee00b
$ ./wpt make-hosts-file | sudo tee -a /etc/hosts
$ cd ../../
$ ./script.py -i ./eval_result_testenv1/6.3_interoracle -o ./eval_result_testenv1/6.3 -b testenv1.txt -r ./firefox/82.0/firefox -m nonoracle
```
- The directory `./eval_result_testenv1/6.3` includes the regression oracle bugs.
- They are classified by their culprit commit (i.e., `B*`).
- You can check PoC files in `./eval_result_testenv1/6.3` directory.
```shell
# Example
$ cat ./eval_result_testenv1/6.3/780992/id:000001.html
<html><head><style>
#htmlvar00002, .class6 { content: url(data:image/gif;base64,R0lGODlhEAAQAMQAAORHHOVSKudfOulrSOp3WOyDZu6QdvCchPGolfO0o/XBs/fNwfjZ0frl3/zy7////wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAkAABAALAAAAAAQABAAAAVVICSOZGlCQAosJ6mu7fiyZeKqNKToQGDsM8hBADgUXoGAiqhSvp5QAnQKGIgUhwFUYLCVDFCrKUE1lBavAViFIDlTImbKC5Gm2hB0SlBCBMQiB0UjIQA7);
</style>
</head><body><input id="htmlvar00002" type="image">
</body></html>
```


### 6.4 Correctness of Rendering Pipeline Analysis
- The data in `r2z2_data/6.4\ Correctness\ of\ Rendering\ Pipeline\ Analysis/` is required to reproduce the result of 6.4.
- The example of reproduction is described below.
```
# Check the info.md file which tells the culprit commit of each file (or issue id).
$ cat ./r2z2_data/6.4\ Correctness\ of\ Rendering\ Pipeline\ Analysis/Style/info.md
| Issue ID | Commit |
|----------|--------|
| 1182587  | 858470 |
| 1185781  | 861868 |
| 1199653  | 873310 |
| 1218770  | 902526 |
```
- Provide the input file using option `-i` and the culprit commit using option `-b` for reproduction. 
- You can check the result from the output directory.
```
# Example
$ python3 src/analyzer.py -i ./r2z2_data/6.4\ Correctness\ of\ Rendering\ Pipeline\ Analysis/Style/Issue_1182587.html -o ./eval_result_testenv1/6.4 -b 858470
```

## Publication
