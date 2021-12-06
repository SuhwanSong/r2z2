 # R2Z2: Detecting Rendering Regressions in Web Browsers through Differential Fuzz Testing

## Setup

The bash file `setup.sh` will install and download all of dependencies for r2z2.
 
```shell
$ ./setup.sh
```


## Reproduction

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
$ python3 
```


### 6.4 Correctness of Rendering Pipeline Analysis

