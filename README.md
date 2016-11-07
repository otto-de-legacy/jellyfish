# Jellyfish
Monitors the health and status of applications running in Marathon or individual services.

## Mode of operation
Jellyfish will visit all configured marathons asynchronously, one thread for every marathon,
  get all the apps and then visit their status page.

All individual configured services will be processed on one extra thread.

## Status Level
Jellyfish knows four status levels:

- 0) **OK**: Everything is fine.
- 1) **UNKNOWN**: App is suspended or Status Page is not available, but app is 'healthy' for Marathon.
- 2) **WARNING**: App is in status 'WARNING'.
- 3) **ERROR**:	App is in status 'ERROR' or there are fewer healthy instances than there should be.

## Job Status Age
If you supply a 'stopped' field in your job information Jellyfish will display the status age (for status other than OK).

## URL Parameter:
### level=[0-3]
Filters applications and jobs by status and only displays application and jobs who met the definded status level or above (worse).

Example: http://jellyfish.com/monitor?level=2

#### jobs=[true/false]
If true, jobs will be displayed. Default is true.

Example: http://jellyfish.com/monitor?jobs=false

#### active_color_only=[true/false]
Show only active color. Default is false.

Example: http://jellyfish.com/monitor?active_color_only=true

#### Filter
The following filter all support comma separated lists. If you want to exclude something, just add an leading **!**.   

Positive filtering always wins, because it excludes everything else.

Example: http://jellyfish.com/monitor?filter=service1,service2

##### filter=[app_name, !app_name]
Filters application names.

##### group=[group_name, !group_name]
Filters groups.

##### type=[type, !type]
Filter for the value of the marathon label "type".

##### env=[environment, !environment]
Filters environments aliase.

#### refresh=[seconds]
Adds metatag to trigger a page refresh every <seconds>.

Example: http://jellyfish.com/monitor?refresh=5

## Dashboard Mode
There is a dashboard mode: /monitor/cinema.

## Configuration

Example:

````
    environments:
      - name: develop
        alias: DEV
      - name: live
        alias: LIVE
    defaults:
      marathons:
        protocol: http
        apps: /v2/apps
        username: some_user
        password: some_password
        root_app_lable: ROOT_LABEL
        status_path_lable: STATUS_PATH_LABEL
        base_domain: some-domain.de
          - ".*marathon-healthcheck"
        graphite:
          - mem: "http://graphite.some-query.de"
          - cpu: "http://graphite.some-query.de"
    marathons:
      - host: marathon.pete.com
      - host: marathon.josh.com
        cookies:
          CookieName: CookieValue
        status_path:
          service_name: https://status_path
    services:
      - id: /develop/vertical/service
        url: http://some_url/status
````
The *defaults* will be merged with the following configuration.

In this example, everything under *defaults/marathons* will be merged with every map below *marathons*.

For more information visit the [Eliza dokumentation](http://eliza.readthedocs.io/en/latest/)

### Vault or Env
To read from Vault or Env use one of the following:

<%= VAULT['secret_path'] %>

<%= ENV['env_name'] %>

## Getting Started

### Obtaining it from source:

````bash
    $ git clone git@github.com:otto-de/jellyfish.git
````

### Installing from source:

````bash
    $ ./setup.sh [OPTIONS]
````
    Options:
        --no-venv   Installs packages globally. May need root privileges.  
        --doc-deps  Includes depedencies to generate documentation.

### Run:

````bash
    $ ./run.py [-h] [-p [PORT]] [-e [ENV]] [-w [WORKDIR]] [-g] [-v [VERBOSE]]

    optional arguments:
      -h, --help                
                            show help message and exit
      -p [PORT], --port [PORT]  
                            Port: Specify port. Default is 8080
      -e [ENV], --env [ENV]     
                            Environment: Specify which config to load. Default is local.
      -w [WORKDIR], --workdir [WORKDIR]
                            Workdir: Specify which working directory to use.
                            Default is the local directory
      -g, --greedy          
                            Greedy: Run processes once (synchron) and then start
                            to serve.
      -v [VERBOSE], --verbose [VERBOSE]
                            Lets you set the loglevel. Application default: ERROR.
                            Option default: INFO
````

### Run tests:

````bash
    $ ./run-tests.sh <environment>
````

## Contribute

Jellyfish is currently in active development and welcomes code improvements, bug fixes, suggestions and feature
requests. 

For those of your interested, providing documentation to other parties is equally welcome.

Please document all notable changes to this project in the provided changelog. Note that this project adheres to [Semantic Versioning](http://semver.org/).

## License

Distributed under the Apache License 2.0
