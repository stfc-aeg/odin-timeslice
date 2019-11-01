# Timeslice Email System

This is the web interface used to send the previously rendered and saved timeslice videos to poeple using an email system in which said videos are found and attatched using the access code provided whent he video is saved.

This code is built up from the code in the odin-control page from the odin-workshop repo, found here: https://github.com/stfc-aeg/odin-workshop and as such the set up is similar to the tutorial laid out on that page. 

the main areas of code in this system are the html file for coding the visuals of the website, the javascript which handles activating/deactivating different parts of the html and checks entered values before sending them to the python file, and the python which handles checking for the existence of access codes and compiling an email with attatchments and the entered email address.

A config file exists in which the path for the location of the rendered videos can be set, along with the ability to format the message recieve in the email itself.


## How to set up

### Create a python 3 virtual environment

```
$ mkvirtualenv -p /usr/local/bin/python3.6 odin-timeslice-3.6 
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
