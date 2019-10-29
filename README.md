# Timeslice Email System

This is the web interface used to send the previously rendered and saved timeslice videos to poeple using an email system in which said videos are found and attatched using the access code provided whent he video is saved.


## How to set up

### Create a python 3 virtual environment

```
$ mkvirtualenv -p /usr/local/bin/python3 odin-timeslice-3 
```

you need to make sure the virtual environment is activated before running the timeslice system

### Clone the Odin-Timeslice from Gitub

``` 
$ git clone git@github.com:stfc-aeg/odin-timeslice.git
$ cd odin-timeslice
```


### Run Setup.py
``` 
$ python setup.py install
``` 

## How to run 
### ensure the virtual environment is activated 
In the directory above /develop
```
$ workon odin-timeslice-3.6
```
### navigate to the odin-timeslice file
```
$ cd develop
$ cd odin-timeslice
```
### run the timeslice system
```
$ odin_server --config test/config/timeslice.cfg
```
### open the web browser
```
localhost:8888
```
