"""

Use datalad to find which subjects have what MRI data files

Possible filetypes:
 - derivatives
    - *ignored*
 - anat
    - sub-<participant_label>[_ses-<session_label>][_acq-<label>][_rec-<label>][_run-<index>]_<modality_label>.nii[.gz]
 - fmap - has lots of options
    - sub-<label>[_ses-<session_label>][_acq-<label>][_run-<run_index>]_
       - phase[12'diff'].nii[.gz]
       - phase[12'diff'].json
       - magnitude[12].nii[.gz]
       - fieldmap.nii[.gz]
       - fieldmap.json
    - sub-<label>[_ses-<session_label>][_acq-<label>]_dir-<dir_label>[_run-<run_index>]_
       - epi.nii[.gz]
       - epi.json
 - func
    - sub-<participant_label>[_ses-<session_label>]_task-<task_label>[_aqc_<label>][_rec-<label>][_run-<index>]_bold.nii[.gz]
 - dwi
    - sub-<participant_label>[_ses-<session_label>][_aqc_<label>][_run-<index>]_dwi.nii[.gz]
    - sub-<participant_label>[_ses-<session_label>][_aqc_<label>][_run-<index>]_dwi.bval
    - sub-<participant_label>[_ses-<session_label>][_aqc_<label>][_run-<index>]_dwi.bvec
    - sub-<participant_label>[_ses-<session_label>][_aqc_<label>][_run-<index>]_dwi.json

acq is an optional argument corresponding to a custom label
rec is an optional argument corresponding to different reconstruction algorithms

"""

import csv
import re
import sys
import os
import argparse
import json
#must import api in this fashion.
#calling datalad.api results in an error
from datalad import api

DATA_TYPES = {
    'anat':re.compile(r"^(?P<subject>sub-[0-9]{6})(?P<session>_ses-[0-9]+)?(?P<acq>_acq-[a-zA-Z0-9-]+)?(?P<rec>_rec-[a-zA-Z0-9-]+)?(?P<run>_run-[a-zA-Z0-9-]+)?_(?P<modality_label>[a-zA-Z0-9-]+)"),
    'fmap':re.compile(r"^(?P<subject>sub-[0-9]{6})(?P<session>_ses-[0-9]+)?(?P<acq>_acq-[a-zA-Z0-9-]+)?(?P<dir>_dir-[a-zA-Z0-9-]+)?(?P<run>_run-[a-zA-Z0-9-]+)?_(?P<modality_label>[a-zA-Z0-9-]+)"),
    'func':re.compile(r"^(?P<subject>sub-[0-9]{6})(?P<session>_ses-[0-9]+)?_task-(?P<task>[a-zA-Z0-9-]+)(?P<acq>_acq-[a-zA-Z0-9-]+)?(?P<rec>_rec-[a-zA-Z0-9-]+)?(?P<run>_run-[a-zA-Z0-9-]+)?_(?P<modality_label>[a-zA-Z0-9-]+)"),
    'dwi':re.compile(r"^(?P<subject>sub-[0-9]{6})(?P<session>_ses-[0-9]+)?(?P<acq>_acq-[a-zA-Z0-9-]+)?(?P<run>_run-[a-zA-Z0-9-]+)?_(?P<modality_label>[a-zA-Z0-9-]+)")
    }

def install_dataset(dataset_id, super_dataset_dir):
    #Install dataset_id into super_dataset_dir/dataset_name, if that folder does not
    # already exist

    # NOTE: if the folder already exists AND is the cwd, running api.install will
    # cause a series of errors only fixable by restarting (as far as I can tell)
    ds_name = os.path.basename(dataset_id)
    ds_path = os.path.join(super_dataset_dir, ds_name)
    if os.path.exists(ds_path):
        raise Exception('Dataset already exists, or %s is already a valid path and would be overwritten' % (ds_path))
    #api.install will report an Exception, but not throw one, if a datalad repository
    # has already been installed at ds_path. I'm not sure it checks to see whether
    # the repository is the expected one or not. The Dataset object it returns appears
    # to mirror the expected one
    # Exception IOError: IOError("Lock at ds_path+'/.git/index.lock' could not be obtained",)
    #   in <bound method AnnexRepo.__del__ of <AnnexRepo path=/datalad_datasets/ds000221 (<class 'datalad.support.annexrepo.AnnexRepo'>)
    #   >> ignored
    ds = api.install(source=dataset_id, path=ds_path, recursive=True, save=False)
    return ds, ds_path

def add_to_dict(dict_name, key, data):
    if key in dict_name:
        dict_name[key].append(data)
    else:
        dict_name[key] = [data]

def check_filename(filename, data_type, subject_name):
    matched = DATA_TYPES[data_type].match(filename)
    if matched == None:
        raise Exception("%s did not match %s expected filename" % (filename, data_type))
    match_dict = matched.groupdict()
    assert match_dict['subject'] == subject_name, "Subject names did not match between folder (%s) and file (%s)" % (subject_name, match_dict['subject'])
    return match_dict

def get_type_neuro_data(dataset_path, subjects={}, add_unknown_subjects=True):
    datatypes = {}
    for dirpath, dirnames, filenames in os.walk(dataset_path):
        if len(dirnames) != 0:
            continue
        dir_path_subsec, data_type  = os.path.split(dirpath)
        if data_type not in DATA_TYPES:
            continue

        dir_path_subsec, session  = os.path.split(dir_path_subsec)
        dir_path_subsec, subject_name  = os.path.split(dir_path_subsec)
        for filename in filenames:
            match_dict = check_filename(filename, data_type, subject_name)
            if data_type == 'func':
                key = data_type+'-bold-'+match_dict['task']
            else:
                key = data_type+'-'+match_dict['modality_label']

            #Add to subjects
            if add_unknown_subjects:
                if subject_name not in subjects:
                    subjects[subject_name] = {}
                add_to_dict(subjects[subject_name], key, os.path.join(dirpath, filename))
            else:
                if subject_name in subjects:
                    add_to_dict(subjects[subject_name], key, os.path.join(dirpath, filename))
                else:
                    continue

            #Add to datatypes
            if key in datatypes:
                datatypes[key].add(subject_name)
            else:
                datatypes[key] = {subject_name}
    return subjects, datatypes

def get_dataset_data(ds, path_to_get, verbose=False, parallelized=None):
    """
    Gets data from dataset (ds) using datalad.api.get()
    Returns a list of file paths to the files that would have been
    downloaded by this command, even if they already existed in the filesystem

    Throws exception if a bad status is returned from datalad.api.get()

    parallelized is either 'None' or an integer describing the number of jobs to
    use (passed directly to datalad.api.get)

    If verbose is True, datalad.api.get will print out the list of files it is
    downloading in json pretty-print
    """
    get_kwargs = {
        'path': path_to_get,
        'dataset': ds,
        'jobs': parallelized
    }
    if verbose:
        get_kwargs['result_renderer'] = 'json_pp'
    specific_data = api.get(**get_kwargs)
    file_paths = []
    for data_file_response in specific_data:
        assert data_file_response['status'] == 'ok', "Requires an 'ok' status, received %s" % (data_file_response['status'])
        if data_file_response['type'] == 'file':
            file_paths.append(data_file_response['path'])
    return file_paths

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_dir", help="Directory to add datalad repository into")
    parser.add_argument("dataset_name", help="Name of datalad repository")
    parser.add_argument("--get_data", nargs='?', default=None, help="Flag indicating whether to get the data")
    args = parser.parse_args()
    print(args)
    ds_name = os.path.basename(args.dataset_name)
    ds_path = os.path.join(args.dataset_dir, ds_name)
    if not os.path.exists(ds_path):
        ds, _ignore = install_dataset(args.dataset_name, args.dataset_dir)
    else:
        ds = api.Dataset(ds_path)
    subjects, datatypes = get_type_neuro_data(ds_path)
    if args.get_data != None:
        file_paths = get_dataset_data(ds, args.get_data)
