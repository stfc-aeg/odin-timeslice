# Timeslice Email System

## How to set up

### Create a python 3 virtual environment

```$ mkvirtualenv -p /usr/local/bin/python3 odin-timeslice-3 ```

you need to make sure the virtual environment is activated before running the timeslice system

### Clone the Odin-Timeslice from Gitub

``` 
$ git clone git@github.com:stfc-aeg/odin-timeslice.git
$ cd odin-timeslice
```


### Run Setup.py
``` 
$ python setup.py develop
``` 

## How to run 
### ensure the virtual environment is activated 
### navigate to the odin-timeslice file
```
cd odin-timeslice
```
### run the timeslice system
```
$ odin_server --config test/config/timeslice.cfg
```
### open the web browser
```
localhost:8888
```
