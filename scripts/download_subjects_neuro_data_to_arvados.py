"""

Use datalad to find which subjects have what MRI data files

"""

import os
import shutil
import argparse
import arvados

import find_subjects_behavior_data
import find_subjects_neuro_data_lite

api = arvados.api('v1')

parser = argparse.ArgumentParser()
parser.add_argument("project_uuid", help="Project to upload data to")
parser.add_argument("output_dir", help="Output directory, where the datalad repository will exist along with any data downloaded")
parser.add_argument("dataset_name", help="Name of datalad repository to clone into")
parser.add_argument("--get-data", action='store_true', help="Flag indicating whether to get the data")
parser.add_argument("--ncores", type=int, nargs='?', default=None, help="If specified, the number of cores to use")
parser.add_argument("-bf", "--behavior-files", help="List of TSV file paths", action='append')
parser.add_argument("-bk", "--behavior-keys", help="List of keys to use for each TSV file", action="append")
args = parser.parse_args()

ds, ds_path = find_subjects_neuro_data_lite.install_dataset(args.dataset_name, args.output_dir)
_ign, complete_subjects, _ign, _ign = find_subjects_behavior_data.get_data(args.behavior_files, args.behavior_keys)
complete_subjects, datatypes = find_subjects_neuro_data_lite.get_type_neuro_data(args.output_dir,
    subjects=complete_subjects, add_unknown_subjects=False)

if args.get_data:
    subject_pdh_uuid = []
    subjects = sorted([s for s in complete_subjects])
    for subject in subjects:
        out = arvados.CollectionWriter()
        subject_get_data_path = os.path.join(ds_path, subject)
        find_subjects_neuro_data_lite.get_dataset_data(ds, subject_get_data_path, parallelized=args.ncores)
        print("Writing %s to new collection" % (subject_get_data_path))
        out.write_directory_tree(subject_get_data_path)
        out.finish()
        print("Written Collection: \n\tPDH: %s\n\n" % (out.portable_data_hash()))
        collection_body = {
            "collection": {
                "name":"%s MPI-Leipzig data" % (subject),
                "owner_uuid":args.project_uuid,
                "portable_data_hash":out.portable_data_hash(),
                "manifest_text":out.manifest_text()
            }
        }
        result = api.collections().create(body=collection_body).execute()
        subject_pdh_uuid.append([subject, result['portable_data_hash'], result['uuid']])

        print("Removing %s to save space" % (subject_get_data_path))
        shutil.rmtree(subject_get_data_path)

    out = arvados.CollectionWriter()
    with out.open('subject_pdh_uuid.txt') as out_file:
        for s_name, pdh, uuid in subject_pdh_uuid:
            out_file.write("%s, %s, %s\n" %(s_name, pdh, uuid))
    out.finish()
    collection_body = {
        "collection": {
            "name":"Subject, PDH, UUID CSV file",
            "owner_uuid":args.project_uuid,
            "portable_data_hash":out.portable_data_hash(),
            "manifest_text":out.manifest_text()
        }
    }
    result = api.collections().create(body=collection_body).execute()
