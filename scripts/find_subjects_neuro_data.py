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
import os
import argparse

import find_subjects_behavior_data
import find_subjects_neuro_data_lite as fndl

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", help="Output directory, where the datalad repository will exist along with any data downloaded")
    parser.add_argument("dataset_name", help="Name of datalad repository to clone into")
    parser.add_argument("--get-data", action='store_true', help="Flag indicating whether to get the data")
    parser.add_argument("--ncores", type=int, nargs='?', default=None, help="If specified, the number of cores to use")
    parser.add_argument("-bf", "--behavior-files", help="List of TSV file paths", action='append')
    parser.add_argument("-bk", "--behavior-keys", help="List of keys to use for each TSV file", action="append")

    args = parser.parse_args()
    print(args)
    ds, ds_path = fndl.install_dataset(args.dataset_name, args.output_dir)
    subjects, complete_subjects, _ignore, _ignore = find_subjects_behavior_data.get_data(args.behavior_files, args.behavior_keys)
    complete_subjects, datatypes = fndl.get_type_neuro_data(args.output_dir, subjects=complete_subjects, add_unknown_subjects=False)
    if args.get_data:
        files_retrieved = []
        for subject in complete_subjects:
            subject_get_data_path = os.path.join(ds_path, subject)
            files_retrieved.extend(fndl.get_dataset_data(ds, subject_get_data_path, parallelized=args.ncores))
