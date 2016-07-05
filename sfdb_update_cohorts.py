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

# Global variables
numWarnings = 0
numContributors = 0
numCohorts = 0

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
    sys.stderr.write("\n=={hdr}== {msg}\n\n".format(hdr=hdr, msg=msg))
    if hdr == "Error":
        exit(1)
    if hdr == "Warning":
        global numWarnings 
        numWarnings += 1

""" Parse the config YAML file """
def read_config(config_file):
    print "Reading config YAML file"
    config = {}
    user_config = yaml.load(config_file)
    for k in CONFIG_DEFAULT:
        v = user_config.get(k)
        if not v:
            print_error("Error", "Configuration value for %s is not specified" %k)
        config[k] = v
    return config

""" Return the chosen DXProject (choice between working, archive, or contributor) """
def access_project(project_id, project_name): 
# Project type: "working", "archive", or "contributor"
# Optional field contributor used only if the project type is "contributor"
    try:
        accessed_proj = dxpy.bindings.DXProject(project_id)
        print "Found %s project" %project_name
        return accessed_proj
    except dxpy.exceptions.DXError, e:
        print_error("Error",
                    "Cannot access %s project. %s" %(project_name, e))


""" Return list of data object type (choice between folders or files) in working project """
def find_proj_data_objects(project, project_name, data_object_type): 
# Project type: "working" or "contributor"; Data object type: "folder" or "file"
    try:
        obj_list = project.list_folder()[data_object_type]
        print "     Found folders (%s)" %obj_list + " in %s project" %project_name
        return obj_list
    except dxpy.exceptions.DXError, e:
        print_error("Error",
                    "Cannot access list of %s in %s project. %s" %(data_object_type, project_name, e))

""" Remove one specified instance of data object type from working project (choice between folders or files) """
def remove_data_object(project_id, project, project_name, data_object_type, data_object):
    if data_object_type == "folder":
        try:
            project.remove_folder(data_object, recurse=True, force=True)
            print "     Removed %s (%s) in %s project (%s)" %(data_object_type, data_object, project_name, project_id)
        except dxpy.exceptions.DXError, e:
            print_error("Error",
                        "Cannot remove %s (%s) in %s project (%s). %s" %(data_object_type, data_object, project_name, project_id, e))

    else: # data_object_type == "file"
        try:
            project.remove_object(data_object, force=True)
            print "     Removed %s (%s) in %s project (%s)" %(data_object_type, data_object, project_name, project_id)
        except dxpy.exceptions.DXError, e:
            print_error("Error",
                        "Cannot remove %s (%s) in %s project (%s). %s" %(data_object_type, data_object, project_name, project_id, e))

""" Create new folder in project """
def create_new_folder(project_id, project, project_name, folder_name):
    try:
        project.new_folder(folder_name, parents=True)
        print "     Creating new folder (%s) in %s project (%s)" %(folder_name, project_name, project_id)
    except dxpy.exceptions.DXError, e:
        print_error("Error",
                    "Cannot create %s project new folder named (%s). %s" %(project_name, project, e))

""" Clone provided list of files (optional: and folders) into specified project """
def clone_files(project_id, project, project_type, folder_name, object_list, folder_list=None):
    try:
        if folder_list is None:
            project.clone(project_id, destination=folder_name, objects=object_list)
            print "         Cloned files (%s) from %s project into %s" %(object_list, project_type, folder_name)
        else:
            project.clone(project_id, destination=folder_name, folders=folder_list, objects=object_list)
            print "         Cloned folders (%s) and files (%s) from %s project into %s" %(folder_list, object_list, project_type, folder_name)
    except dxpy.exceptions.DXError, e:
            print_error("Error",
                        "Cannot clone  folders (%s) and files (%s) from %s project into %s. %s" %(folder_list, object_list, project_type, folder_name,e))

""" Finds and returns the summaryfile object in specified folder """
def find_and_clone_summaryfile(project_id, project, project_name, folder, contributor_folder):
    try:
        summaryfile = dxpy.bindings.search.find_one_data_object(classname="file", name="summaryfile.txt", project=project.get_id(), folder=folder, zero_ok=False, more_ok=False)
        print "         Found one summaryfile.txt in contributor project (%s) and folder (%s)" %(project_name, folder)
        clone_files(project_id, project, project_name, contributor_folder, [summaryfile['id']])
    except dxpy.exceptions.DXSearchError, e:
        print_error("Warning",
                    "Contributor project (%s) has a folder (%s) with zero or multiple summaryfile.txt files). %s" %(project_name, folder, e))
        return

def print_exit_message(archive_folder):
    print "\n============== SFDB Update Successful =============="
    if numWarnings > 0:
        print "%d WARNINGS DETECTED: REFER TO LOGS FOR WARNING MESSAGE\n" %numWarnings
    print "Working project has been updated with %d cohort summaryfile.txt files" %numCohorts + " from %d contributor projects" %numContributors
    print "New archive folder (%s) has been created to store previous version of the working project.\n" %archive_folder.lstrip('/')

""" Archive files in the working SFDB project """
def archive_current_files(config):
    # Access working and archive projects
    working_proj = access_project(config['working_project'], "working")
    archive_proj = access_project(config['archive_project'], "archive")

    # Find list of all folders and files in working project
    folder_list = find_proj_data_objects(working_proj, "working", "folders")
    object_list = find_proj_data_objects(working_proj, "working", "objects")

    # Create new timestamp-labeled folder in archive project
    timestamp_folder = time.strftime("/%Y-%m/%d-%H-%M-%S")
    create_new_folder(config['archive_project'], archive_proj, "archive", timestamp_folder)

    # Clone all folders and files from the working project into the new folder in archive project
    clone_files(config['archive_project'], working_proj, "working", timestamp_folder, object_list, folder_list)
    return timestamp_folder

def update_working_project(config):
    # Access working project
    working_proj = access_project(config['working_project'], "working")

    # Find list of all folders and files in working project
    folder_list = find_proj_data_objects(working_proj, "working", "folders")
    object_list = find_proj_data_objects(working_proj, "working", "objects")

    # Remove all folders and files in the working SFDB project
    for folder in folder_list:
        remove_data_object(config['working_project'], working_proj, "working", "folder", folder)
    for file in object_list:
        remove_data_object(config['working_project'], working_proj, "working", "file", file)

    for contributor in config['contributors']:
        # Consolidate summaryfile.txt files from all contributors
        contributor_proj = access_project(config['contributors'][contributor], contributor)
        folder_list = find_proj_data_objects(contributor_proj, contributor, "folders")
        global numContributors 
        numContributors += 1

        for folder in folder_list:
            # Create new folder for each cohort of each contributor
            contributor_folder =("/%s" %contributor + "_%s" %folder.lstrip('/').replace(" ", "")) # Strips whitespace
            create_new_folder(config['working_project'], working_proj, "working", contributor_folder)
            global numCohorts 
            numCohorts += 1

            # Clone the summaryfile.txt from the contributor cohort into the new folder in working project
            summaryfile = find_and_clone_summaryfile(config['working_project'], contributor_proj, contributor, folder, contributor_folder)

""" Main entry point """
def main():
    args = parse_args()
    config = read_config(args.config)
    archive_folder = archive_current_files(config)
    update_working_project(config)
    print_exit_message(archive_folder)

if __name__ == "__main__":
    main()
