import argparse
import dxpy
import time
import yaml
import sys

CONFIG_DEFAULT = {
    'archive_project': 'project-BxVXgF80VjVbZ1QfF0PKzFxk',
    'contributors': {},
    'working_project': 'project-BxVK4Q8081jfqjyXfxGyQVbV'
}

""" Parse command line arguments """
def parse_args():

    parser = argparse.ArgumentParser(description='This script syncs genotype frequency databases' +
                                                 ' from data contributors of the SG Federated Database' +
                                                 ' project to a common admin project.',
                                     formatter_class=argparse.RawTextHelpFormatter)

    requiredNamed = parser.add_argument_group("Required named arguments")

    requiredNamed.add_argument('--config', '-c', metavar = "CONFIG_FILE",
                        help='Path to config YAML file',
                        type=argparse.FileType('r'),
                        required=True)

    return parser.parse_args()

""" Print error message to stderr, exiting with non-zero state if hdr
type is 'Error'."""
def print_error(hdr, msg):
    sys.stderr.write("=={hdr}== {msg}\n".format(hdr=hdr, msg=msg))
    if hdr == "Error":
        exit(1)

""" Parse the config YAML file """
def read_config(config_file):
    config = {}
    user_config = yaml.load(config_file)
    for k in CONFIG_DEFAULT:
        v = user_config.get(k)
        if not v:
            print_error("Error", "Configuration value for {opt} is not specified".format(opt=k))
        config[k] = v
    return config

""" Archive files in the working SFDB project """
def archive_current_files(config):

    try:
        working_proj = dxpy.bindings.DXProject(config['working_project'])
    except dxpy.exceptions.DXError, e:
        print_error("Error",
                    "Cannot access working project given ({0}). {1}".format(project, str(e)))

    try:
        archive_proj = dxpy.bindings.DXProject(config['archive_project'])
    except dxpy.exceptions.DXError, e:
        print_error("Error",
                    "Cannot access archival project given ({0}). {1}".format(project, str(e)))


    timestamp_folder = time.strftime("/%Y-%m/%d-%H%M%S")

    folder_list = working_proj.list_folder()['folders']
    object_list = working_proj.list_folder()['objects']

    archive_proj.new_folder(timestamp_folder, parents=True)
    working_proj.clone(config['archive_project'], destination=timestamp_folder, folders=folder_list, objects=object_list)

# Consolidates all files/folders from contributors into working SFDB project.
# Deletes all working SFDB project files before the consolidation step.
def update_working_project(config):

    try:
        working_proj = dxpy.bindings.DXProject(config['working_project'])
    except dxpy.exceptions.DXError, e:
        print_error("Error",
                    "Cannot access working project given ({0}). {1}".format(project, str(e)))

    for contributor in config['contributors']:
        try:
            contributor_proj = dxpy.bindings.DXProject(config['contributors'][contributor])
        except dxpy.exceptions.DXError, e:
            print_error("Error",
                    "Cannot access contributor project given ({0}). {1}".format(project, str(e)))
            
        contributor_folder = ("/%s" %contributor)    
        folder_list = contributor_proj.list_folder()['folders']
        object_list = contributor_proj.list_folder()['objects']

        working_proj.remove_folder(contributor_folder, recurse=True, force=True)
        working_proj.new_folder(contributor_folder, parents=True)
        contributor_proj.clone(config['working_project'], destination=contributor_folder, folders=folder_list, objects=object_list)

""" Main entry point """
def main():
    args = parse_args()
    config = read_config(args.config)
    archive_current_files(config)
    update_working_project(config)

if __name__ == "__main__":
    main()
