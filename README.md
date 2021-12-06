# r2z2

## Setup

The bash file `setup.sh` will install and download all of dependencies for r2z2.
 
```shell
./setup.sh
```


## Reproduction

### 6.1 Effectiveness of Change Detection

#### Test Env 1

```
# How to run fuzzer
python3 src/r2z2.py -i ./testenv1/seeds -o ./testenv1/change_detector -b ./testenv1/chrome_vers.txt -j 24
```

```
# Fuzzing Log
cat ./testenv1/change_detector/fuzz_log.txt
```


#### Test Env 2
```
# How to run fuzzer
python3 src/r2z2.py -i ./testenv2/seeds -o ./testenv2/change_detector -b ./testenv2/chrome_vers.txt -j 24
```

### 6.2 Effectiveness of Bisect Analysis
