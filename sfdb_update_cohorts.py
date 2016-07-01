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
            print_error("Error", "Configuration value for %s is not specified" %k)
        config[k] = v
    return config

""" Return the chosen DXProject (choice between working, archive, or contributor) """
def access_project(config, project_type, contributor=None): 
# Project type: "working", "archive", or "contributor"
# Optional field contributor used only if the project type is "contributor"

    if project_type == "working":
        try:
            working_proj = dxpy.bindings.DXProject(config['working_project'])
        except dxpy.exceptions.DXError, e:
            print_error("Error",
                        "Cannot access working project given (%s" %config['working_project'] + "). %s" %e)
        print "Found working project (%s)" %config['working_project']
        return working_proj

    elif project_type == "archive":
        try:
            archive_proj = dxpy.bindings.DXProject(config['archive_project'])
        except dxpy.exceptions.DXError, e:
            print_error("Error",
                        "Cannot access archival project given (%s" %config['archive_project'] + "). %s"%e)
        print "Found archive project (%s)" %config['archive_project']
        return archive_proj

    elif project_type == "contributor":
        try:
            contributor_proj = dxpy.bindings.DXProject(config['contributors'][contributor])
        except dxpy.exceptions.DXError, e:
            print_error("Error",
                        "Cannot access contributor project given (%s)" %contributor + ". %s" %e)
        print "Found contributor project (%s)" %contributor
        return contributor_proj

    else:
        print_error("Error",
                    "Cannot access project type given (%s)." %project_type)

""" Return list of data object type (choice between folders or files) in working project """
def find_proj_data_objects(config, project, project_type, data_object_type, contributor=None): 
# Project type: "working" or "contributor"; Data object type: "folder" or "file"

    if project_type == "contributor" and data_object_type == "folder":
        contributor_proj = project
        try:
            folder_list = contributor_proj.list_folder()['folders']
        except dxpy.exceptions.DXError, e:
            print_error("Error",
                        "Cannot access list of folders in contributor project (%s" %contributor +"). %s" %e)
        print "     Found folders (%s)" %folder_list + " in contributor project %s" %contributor
        return folder_list

    working_proj = project
    if data_object_type == "folder":
        try:
            folder_list = working_proj.list_folder()['folders']
        except dxpy.exceptions.DXError, e:
            print_error("Error",
                        "Cannot access list of folders in working project (%s" %config['working_project'] +"). %s" %e)
        print "     Found folders (%s)" %folder_list + " in working project %s" %config['working_project']
        return folder_list

    elif data_object_type == "file":
        try:
            object_list = working_proj.list_folder()['objects']
        except dxpy.exceptions.DXError, e:
            print_error("Error",
                        "Cannot access list of objects in working project (%s" %config['working_project'] +"). %s" %e)
        print "     Found objects (%s)" %object_list + " in working project %s" %config['working_project']
        return object_list

    else:
        print_error("Error",
                    "Cannot access data object type given (%s)." %data_object_type)

""" Remove one specified instance of data object type from working project (choice between folders or files) """
def remove_working_proj_data_object(config, working_proj, data_object_type, data_object):
    if data_object_type == "folder":
        folder = data_object
        try:
            working_proj.remove_folder(folder, recurse=True, force=True)
        except dxpy.exceptions.DXError, e:
            print_error("Error",
                        "Cannot remove folder (%s" %folder + "). %s" %e + "in working project %s." %config['working_project'])
        print "     Removed folder (%s)" %folder + " in working project (%s)" %config['working_project']

    elif data_object_type == "file":
        file = data_object
        try:
            working_proj.remove_object(file, force=True)
        except dxpy.exceptions.DXError, e:
            print_error("Error",
                        "Cannot remove object (%s" %file + "). %s" %e + "in working project %s." %config['working_project'])
        print "     Removed object (%s)" %file + " in working project (%s)" %config['working_project']

    else:
        print_error("Error",
                    "Cannot remove data object type given (%s)." %data_object)

""" Create new folder in project """
def create_new_folder(config, project, project_type, folder_name):
# Destination project type: "working" or "archive"; Project: DXProject object; 

    if project_type == "archive":
        timestamp_folder = folder_name
        archive_proj = project
        try:
            archive_proj.new_folder(timestamp_folder, parents=True)
        except dxpy.exceptions.DXError, e:
            print_error("Error",
                        "Cannot create archive project new folder named (%s" %timestamp_folder + "). %s" %e)
        print "     Creating new folder (%s" %timestamp_folder + ") in archive project (%s)" %config['archive_project']

    elif project_type == "working":
        contributor_folder = folder_name
        working_proj = project
        try:
            working_proj.new_folder(contributor_folder, parents=True)
        except dxpy.exceptions.DXError, e:
            print_error("Error",
                        "Cannot create working project new folder named (%s" %contributor_folder + "). %s" %e)
        print "     Creating new folder (%s" %contributor_folder + ") in working project (%s)" %config['working_project']

""" Clone provided list of files (optional: and folders) into specified project """
# Project type: "working" or "archive"; Originating project: DXProject object; Destination folder name: Existing folder
def clone_files(config, project, project_type, folder_name, object_list, folder_list=None, contributor=None):
    if project_type == "working":
        working_proj = project
        timestamp_folder = folder_name
        try:
            working_proj.clone(config['archive_project'], destination=timestamp_folder, folders=folder_list, objects=object_list)
        except dxpy.exceptions.DXError, e:
            print_error("Error",
                        "Cannot clone folders (%s" %folder_list + ") to destination (%s" %timestamp_folder + "). %s" %e)
        print "         Cloned folders (%s)" %folder_list + " and files (%s)" %object_list + " from working project (%s" %config['working_project'] + ") into archive project folder (%s)" %timestamp_folder

    elif project_type == "contributor":
        contributor_proj = project
        contributor_folder = folder_name
        try:
            contributor_proj.clone(config['working_project'], destination=contributor_folder, objects=[object_list.get('id')])
        except dxpy.exceptions.DXError, e:
            print_error("Error",
                        "Cannot clone summaryfile.txt from contributor project (%s)" %contributor + " to destination (%s)." %contributor_folder[1:])
        print "         Cloned summaryfile.txt from contributor project (%s)" %contributor + " into working project (%s)" %contributor_folder

""" Finds and returns the summaryfile object in specified folder """
def find_summaryfile(contributor_proj, contributor, folder):
    try:
        summaryfile = dxpy.bindings.search.find_one_data_object(classname="file", name="summaryfile.txt", project=contributor_proj.get_id(), folder=folder, zero_ok=False, more_ok=False)
    except dxpy.exceptions.DXSearchError, e:
        print_error("Warning",
                    "Contributor project (%s" %contributor + ") has a folder (%s) with zero or multiple summaryfile.txt files" %folder + "). %s" %e)
    print "         Found one summaryfile.txt in contributor project (%s" %contributor + ") and folder (%s)" %folder
    return summaryfile

def successful_exit():
    print "\nWorking project has been updated with all cohort summaryfile.txt files"
    print "New archive folder has been created to store previous version of the working project\n"

""" Archive files in the working SFDB project """
def archive_current_files(config):
    # Access working and archive projects
    working_proj = access_project(config, "working")
    archive_proj = access_project(config, "archive")

    # Find list of all folders and files in working project
    folder_list = find_proj_data_objects(config, working_proj, "working", "folder")
    object_list = find_proj_data_objects(config, working_proj, "working", "file")

    # Create new timestamp-labeled folder in archive project
    timestamp_folder = time.strftime("/%Y-%m/%d-%H-%M-%S")
    create_new_folder(config, archive_proj, "archive", timestamp_folder)

    # Clone all folders and files from the working project into the new folder in archive project
    clone_files(config, working_proj, "working", timestamp_folder, object_list=object_list, folder_list=folder_list)

def update_working_project(config):
    # Access working project
    working_proj = access_project(config, "working")

    # Find list of all folders and files in working project
    folder_list = find_proj_data_objects(config, working_proj, "working", "folder")
    object_list = find_proj_data_objects(config, working_proj, "working", "file")

    # Remove all folders and files in the working SFDB project
    for folder in folder_list:
        remove_working_proj_data_object(config, working_proj, "folder", folder)
    for file in object_list:
        remove_working_proj_data_object(config, working_proj, "file", file)

    for contributor in config['contributors']:
        # Consolidate summaryfile.txt files from all contributors
        contributor_proj = access_project(config, "contributor", contributor=contributor)
        folder_list = find_proj_data_objects(config, contributor_proj, "contributor", "folder", contributor=contributor)

        for folder in folder_list:
            # Create new folder for each cohort of each contributor
            contributor_folder =("/%s" %contributor + "_%s" %folder.lstrip('/').replace(" ", "")) # Strips whitespace
            create_new_folder(config, working_proj, "working", contributor_folder)

            # Clone the summaryfile.txt from the contributor cohort into the new folder in working project
            summaryfile = find_summaryfile(contributor_proj, contributor, folder)
            clone_files(config, contributor_proj, "contributor", contributor_folder, object_list=summaryfile, contributor=contributor)

""" Main entry point """
def main():
    args = parse_args()
    config = read_config(args.config)
    archive_current_files(config)
    update_working_project(config)
    successful_exit()

if __name__ == "__main__":
    main()
