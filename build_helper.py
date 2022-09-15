#!/usr/bin/env python3

"""
This script should be used for deployment
of apps to the Docker Swarm.

It will do the following, given a 
yml (swarm stack deployment) file as input:

* Make sure required labels are set in YML file.
* Make sure there are no conflicting labels for a different app in the YML file
* Inject new labels containing github repo, app owner email, etc.
* TODO: Add this app to a monitoring system (if it hasn't been added already)
  that will alert app owner (and scicomp?) if app container(s) goes down.

The script will generate an output yml file as
its standard output. 
The script should be called in build_test
for validation. It can either be called again
in the deploy stage (main branch) or its output
yml file, generated in build_test, can be reused.


"""

import os
import sys
import yaml



def main():
    "do the work"
    with open(sys.argv[1]) as file:
        yml = yaml.safe_load(file)
    errors = []
    if not 'networks' in yml:
        errors.append("No networks defined")
    networks = yml['networks']
    if not 'backend' in networks or not networks['backend'] is None:
        errors.append("Must have 'backend' network defined with no value")
    # TODO proxy network
    # TODO both networks in main service
    # TODO consistent app name in main service
    # TODO app name should not be used by any other app (how do we do this?)

    main_service = None
    for service_name, service in yml['services'].items():
        if 'deploy' in service and 'labels' in service['deploy']:
            main_service = service
            break
    if not main_service:
        raise Exception("No service found with deploy.labels")
    labels = main_service['deploy']['labels']
    if not 'traefik.enable=true' in labels:
        raise Exception("traefik.enable label not set")
    
    # inject stuff
    github_url = os.getenv('CI_PROJECT_URL').replace(".ci.fredhutch.org", "github.com")
    labels.append(f"org.fredhutch.app.github_url={github_url}")
    labels.append(f"org.fredhutch.app.owner={os.getenv('CI_COMMIT_AUTHOR')}")
    print(yaml.dump(yml))

if __name__ == "__main__":
    main()


