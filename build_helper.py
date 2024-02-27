#!/usr/bin/env python3

"""
This script should be used for deployment
of apps to the Docker Swarm.

It will do the following, given a 
yml (swarm stack deployment) file as input:

* Make sure required labels are set in YML file.
* Make sure there are no conflicting labels for a different app in the YML file
* Inject new labels containing github repo, app owner email, 
  logging config, etc.
* TODO: Add this app to a monitoring system (if it hasn't been added already)
  that will alert app owner (and scicomp?) if app container(s) goes down.

The script will generate an output yml file as
its standard output. 
The script should be called in the test stage
for validation; it will exit with a non-zero code
if there is an error.
It can either be called again
in the deploy stage (main branch) or its output
yml file, generated in test, can be reused.


"""
import argparse
import os
import sys
import yaml



def main():
    "do the work"
    parser = argparse.ArgumentParser(description='Validate and/or inject data into a swarm stack deployment file')
    parser.add_argument('--no-network-check', action='store_true', help='Do not check for proxy network')
    parser.add_argument('--fluentd-logging', action='store_true', help='Use fluentd logging')
    parser.add_argument('yml_file', help='YML file to validate/inject')
    args = parser.parse_args()
    with open(args.yml_file) as file:
        yml = yaml.safe_load(file)
    if not args.no_network_check:
        if not 'networks' in yml:
            raise Exception("No networks defined")
        networks = yml['networks']
        # TODO should we be checking this or just adding it?
        if not 'proxy' in networks or not networks['proxy'] ==  dict(external=True):
            raise Exception("Must have 'proxy' network defined as external: true")
    # TODO consistent app name in main service

    main_services = []
    for service_name, service in yml['services'].items():
        if 'deploy' in service and 'labels' in service['deploy']:
            main_services.append(service)
    if not main_services:
        raise Exception("No services found with deploy.labels")
    for service in main_services:
        labels = service['deploy']['labels']
        if not 'traefik.enable=true' in labels:
            raise Exception("traefik.enable label not set")
        if not args.no_network_check:
            if not 'networks' in service:
                raise Exception("No networks defined for main service")
            if not 'proxy' in service['networks']:
                raise Exception("proxy network not defined for main service")
        
        # inject stuff
        github_url = os.getenv('CI_PROJECT_URL').replace("ci.fredhutch.org", "github.com")
        labels.append(f"org.fredhutch.app.github_url={github_url}")
        labels.append(f"org.fredhutch.app.owner={os.getenv('CI_COMMIT_AUTHOR')}")
        labels.append(f"org.fredhutch.app.name={os.getenv('CI_PROJECT_NAME')}")

        if args.fluentd_logging:
            # fluentd logging will allow the app developer to 
            # see the app logs even if they do not have access
            # to our gitlab instance. it also forwards logs to
            # splunk. see https://github.com/FredHutch/sc-fluentd.git
            for var in ['FLUENTD_HOST', 'FLUENTD_PORT']:
                if not os.getenv(var):
                    raise Exception(f"{var} not set")

            for servicename, service in yml['services'].items():
                service['logging'] = dict(driver='fluentd')
                service['logging']['options'] = {}
                service['logging']['options']['fluentd-address'] = f"{os.getenv('FLUENTD_HOST')}:{os.getenv('FLUENTD_PORT')}"
                service['logging']['options']['tag'] = f"docker.{os.getenv('CI_PROJECT_NAME')}"
        else: # splunk logging - the default
            # do logging for each service
            if not os.getenv('SPLUNK_TOKEN'):
                raise Exception("SPLUNK_TOKEN not set")
            if not os.getenv('SPLUNK_URL'):
                raise Exception("SPLUNK_URL not set")

            for servicename, service in yml['services'].items():
                service['logging'] = dict(driver='splunk')
                service['logging']['options'] = {}
                service['logging']['options']['splunk-token'] = os.getenv('SPLUNK_TOKEN')
                service['logging']['options']['splunk-url'] = os.getenv('SPLUNK_URL')
                service['logging']['options']['tag'] = f"{os.getenv('CI_PROJECT_NAME')}/{servicename}"
    print(yaml.dump(yml))

if __name__ == "__main__":
    main()


