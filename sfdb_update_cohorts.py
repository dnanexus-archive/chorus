import argparse
import dxpy
import time
import yaml
import sys

# Note: this archiving script will not copy summaryfile.txt files from the working SFDB project if
# they have the same file IDs as pre-existing files in the archive SFDB project.

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
    print "Reading config YAML file"
    config = {}
    user_config = yaml.load(config_file)
    for k in CONFIG_DEFAULT:
        v = user_config.get(k)
        if not v:
            print_error("Error", "Configuration value for {opt} is not specified".format(opt=k))
        config[k] = v
    return config

""" Archive files in the working SFDB project """
# Error handling: (1) Access errors, (2) Incorrect number of summaryfile.txt 
# Deletes all working SFDB project files after archiving
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

    timestamp_folder = time.strftime("/%Y-%m/%d-%H-%M-%S")

    folder_list = working_proj.list_folder()['folders']
    archive_proj.new_folder(timestamp_folder, parents=True)
    print "Creating new folder in archive project: %s" %timestamp_folder[1:]
    working_proj.clone(config['archive_project'], destination=timestamp_folder, folders=folder_list)
    for folder in folder_list:
        print "     Copied folder from working project into archive project: %s" %folder[1:]

# Consolidates all summaryfile.txt from contributors into working SFDB project.
# Error handling: (1) Access errors, (2) Incorrect number of summaryfile.txt
def update_working_project(config):
    working_proj = dxpy.bindings.DXProject(config['working_project'])
    folder_list = working_proj.list_folder()['folders']
    object_list = working_proj.list_folder()['objects']
    # Remove all folders and files in the working SFDB project
    for folder in folder_list:
        working_proj.remove_folder(folder, recurse=True, force=True)
    for file in object_list:
        working_proj.remove_object(file, force=True)
    # Consolidate summaryfile.txt files from all contributors
    for contributor in config['contributors']:
        print "Accessing files in contributor project: %s" %contributor

        try:
            contributor_proj = dxpy.bindings.DXProject(config['contributors'][contributor])
        except dxpy.exceptions.DXError, e:
            print_error("Error 1: ",
                    "Cannot access contributor project given ({0}). {1}".format(project, str(e)))

        folder_list = contributor_proj.list_folder()['folders']
        for folder in folder_list:
            contributor_folder =("/%s" %contributor + "_%s" %folder[1:])
            working_proj.new_folder(contributor_folder, parents=True)
            print "     Creating new folder in working project: %s" %contributor_folder[1:]
            summaryfile = dxpy.bindings.search.find_one_data_object(classname="file", name="summaryfile.txt", project=contributor_proj.get_id(), folder=folder, zero_ok=False, more_ok=False)
            contributor_proj.clone(config['working_project'], destination=contributor_folder, objects=[summaryfile.get('id')])
            print "     Copied summaryfile.txt from contributor project %s" %contributor + " into working project: %s" %contributor_folder[1:]

""" Main entry point """
def main():
    args = parse_args()
    config = read_config(args.config)
    archive_current_files(config)
    update_working_project(config)

if __name__ == "__main__":
    main()
