"""

Use datalad to find which subjects have what MRI data files

"""

import os
import shutil
import argparse
import arvados

import find_subjects_behavior_data
import find_subjects_neuro_data

project_uuid = "qr1hi-j7d0g-u5mez5ad2fb3gn8"
api = arvados.api('v1')

parser = argparse.ArgumentParser()
parser.add_argument("output_dir", help="Output directory, where the datalad repository will exist along with any data downloaded")
parser.add_argument("dataset_name", help="Name of datalad repository to clone into")
parser.add_argument("--get-data", action='store_true', help="Flag indicating whether to get the data")
parser.add_argument("--ncores", type=int, nargs='?', default=None, help="If specified, the number of cores to use")
parser.add_argument("-bf", "--behavior-files", help="List of TSV file paths", action='append')
parser.add_argument("-bk", "--behavior-keys", help="List of keys to use for each TSV file", action="append")
args = parser.parse_args()
ds, ds_path = find_subjects_neuro_data.install_dataset(args.dataset_name, args.output_dir)
subjects, complete_subjects, _ignore, _ignore = find_subjects_behavior_data.get_data(args.behavior_files, args.behavior_keys)
complete_subjects, datatypes = find_subjects_neuro_data.get_type_neuro_data(args.output_dir,
    subjects=complete_subjects, add_unknown_subjects=False)
if args.get_data:
    files_retrieved = []
    out = arvados.CollectionWriter()
    for subject in complete_subjects:
        subject_get_data_path = os.path.join(ds_path, subject)
        files_retrieved.extend(find_subjects_neuro_data.get_dataset_data(ds,
            subject_get_data_path, parallelized=args.ncores))
        print("Writing %s to Collection" % (subject_get_data_path))
        out.write_directory_tree(subject_get_data_path)
        out.finish_current_stream()
        print("Current Collection: \nPDH: %s\n\nManifest text: %s\n\n" % (out.portable_data_hash(), out.manifest_text()))
        print("Removing %s to save space" % (subject_get_data_path))
        shutil.rmtree(subject_get_data_path)
    coll_id = out.finish()
    collection_body = {
        "collection": {
            "name":"MPI-Leipzig data",
            "owner_uuid":project_uuid,
            "portable_data_hash":out.portable_data_hash(),
            "manifest_text":out.manifest_text()
        }
    }
    result = api.collections().create(body=collection_body).execute()
