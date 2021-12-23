 # R2Z2: Detecting Rendering Regressions in Web Browsers through Differential Fuzz Testing
 
## Table
1. [Environment](#Environment)
2. [Setup](#Setup)
3. [Usage](#Usage)
4. [Reproduction](#Reproduction)
5. [Publication](#Publication)

## Environment
- Ubuntu 18.04 64bit

## Setup
You need to install the dependencies of R2Z2, and then
download target browsers and reference browser with their drivers. 

Each driver should be placed in the same directory of browser binary.

The bash file `setup.sh` will install all of dependencies and download the browsers.
```shell
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

####  1. Change Detector 
- The change detector finds the candidate html bugs from the seeds html files.
- You should provide the paths of target browser to the "browser_pathfile".
```
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
$ ./script.py -i [inter_oracle_output_dir] -o [oracle_output_dir] -b [browser_pathfile] -r [ref_browser_path] -m nonoracle
```

#### 6. Rendering Pipeline Analysis
- The rendering pipeline analysis identifies the culprit stage of oracle bug and provides the diff information.
```
$ ./script.py -i [oracle_output_dir] -o [analysis_output_dir] -m pipeline
```

## Reproduction

### Setup
```shell
$ ./setup.sh repro
```

### 6.1 Effectiveness of Change Detection

#### Test Environment 1

- To reproduce the result of 6.1, please run the following command:
```
$ python3 src/r2z2.py -i ./testenv1/seeds -o ./testenv1/change_detector -b ./testenv1/chrome_vers.txt -j 24
```

- The directory `./testenv1/seeds` has 200K HTML inputs used in the paper.
- The directory `./testenv1/change_detector/` includes the 
candidate html files found by R2Z2, e.g., `thread-00/id:000000_BUG.html`
- It also includes `fuzz_log.txt` file, which recorded the number of tested HTML 
files and candidate html files over the time during fuzzing.
- To check the result, please run the following command: 
```
$ cat ./testenv1/change_detector/fuzz_log.txt
Time(s), Tested HTMLs, CandBug
0.010046958923339844, 0, 0

...

6306.686718702316, 199998, 6785
```



#### Test Environment 2

- To reproduce the result of 6.1, please run the following command:
```
$ python3 src/r2z2.py -i ./testenv2/seeds -o ./testenv2/change_detector -b ./testenv2/chrome_vers.txt -j 24
```

- The directory `./testenv2/seeds` has 200K HTML inputs used in the paper.
- The directory `./testenv2/change_detector/` includes the 
candidate html files found by R2Z2, e.g., `thread-00/id:000000_BUG.html`
- It also includes `fuzz_log.txt` file, which recorded the number of tested HTML 
files and candidate html files over the time during fuzzing.
- To check the result, please run the following command: 
```
$ cat ./testenv2/change_detector/fuzz_log.txt
Time(s), Tested HTMLs, CandBug
0.01497030258178711, 0, 0

...

8418.58963561058, 200000, 16205
```

### 6.2 Effectiveness of Bisect Analysis

#### Test Environment 1
- To reproduce the result of 6.2, please run the following command:
```
$ python3 src/bisector.py -i ./testenv1/change_detector -o ./testenv1/bisect -j 18 --download -s 766000 -e 784091
```


### 6.3 Effectiveness of Regression Oracle

#### Test Environment 1
- To reproduce the result of 6.3, please run the following command:
```
# Interoperability Oracle
$ python3 repro.py -i [] -o [] -r ./firefox/82.0/firefox -m interoracle


# Non-feature-update Oracle
$ ./wpt make-hosts-file | sudo tee -a /etc/hosts
$ python3 src/nfuoracle.py -i [] -b [] -r ./firefox/82.0/firefox
```

### 6.4 Correctness of Rendering Pipeline Analysis
- To reproduce the result of 6.4, please run the following command:
```


```


## Publication
