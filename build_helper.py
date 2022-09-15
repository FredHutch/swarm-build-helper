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

import sys
import yaml



def main():
    "do the work"
    with open(sys.argv[1]) as file:
        yml = yaml.safe_load(file)
    print(yml)
    import IPython; IPython.embed()
    main_service = None
    for service in yml['services']:
        if 'deploy' in service and 'labels' in service['deploy']:
            main_service = service
            break
        print(service)
    if not main_service:
        raise Exception("No service found with deploy.labels")

if __name__ == "__main__":
    main()


