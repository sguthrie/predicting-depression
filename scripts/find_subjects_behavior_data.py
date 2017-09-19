"""

"""

import csv
import re
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt

def check_valid_value(key, val):
    if key == "participant_id":
        if re.match(r'sub-[0-9]{6}', val) is None:
            return False
        return True
    # "else" statements not necessary because function always returns if the "if"
    # statement evaluates to True
    if val == "n/a":
        return True
    try:
        float(val)
        return True
    except ValueError:
        return False

def add_to_subjects(subjects, subject_data, behavior_name):
    subject_name = subject_data["participant_id"]
    behavior_data = float(subject_data[behavior_name])
    if subject_name in subjects:
        subjects[subject_name][behavior_name] = behavior_data
    else:
        subjects[subject_name] = {behavior_name:behavior_data}

def find_subjects_with_reported_behavior(subjects, behavior_name, filepath):
    assert type(subjects) == dict
    assert type(behavior_name) == str

    with open(filepath, 'r') as tsv:
        tsv = csv.DictReader(tsv, delimiter='\t')
        for subject in tsv:
            assert behavior_name in subject, \
                "Unable to find %s in subject %s for file %s" % (behavior_name,
                    subject["participant_id"], filepath)
            for key in subject:
                assert check_valid_value(key, subject[key]), \
                    "%s is an unexpected value for subject %s for key %s (%s)" % (subject[key],
                    subject["participant_id"], key, filepath)
            if subject[behavior_name] != "n/a":
                add_to_subjects(subjects, subject, behavior_name)
    return subjects

def get_data(behavior_paths, behavior_keys):
    assert len(behavior_paths) == len(behavior_keys), "Behavior files must be matched \
        one-to-one with behavior keys. Number of behavior files: %i. \
        Number of behavior keys: %i" % (len(behavior_paths), len(behavior_keys))
    subjects = {}
    for path, behavior_key in zip(behavior_paths, behavior_keys):
        subjects = find_subjects_with_reported_behavior(subjects, behavior_key, path)
    num_subjects_with_all_data = 0
    complete_subjects = {}
    raw_data = {behavior_key:[] for behavior_key in behavior_keys}
    complete_raw_data = {behavior_key:[] for behavior_key in behavior_keys}
    for subject in subjects:
        for behavior_key in behavior_keys:
            if behavior_key in subjects[subject]:
                raw_data[behavior_key].append(subjects[subject][behavior_key])
        if len(subjects[subject]) == len(behavior_paths):
            num_subjects_with_all_data += 1
            complete_subjects[subject] = subjects[subject]
            for behavior_key in behavior_keys:
                complete_raw_data[behavior_key].append(subjects[subject][behavior_key])
    print("%i subjects have data in all given files" % num_subjects_with_all_data)
    return subjects, complete_subjects, raw_data, complete_raw_data

def draw_figure(behavior_keys, raw_data, complete_raw_data, autoscale=True):
    if autoscale:
        plt.figure(figsize=(6,len(behavior_keys)*4))
    plt.subplot(len(behavior_keys),2,1)
    plt.title("All data")
    plt.subplot(len(behavior_keys),2,2)
    plt.title("Complete data")
    for i, behavior_key in enumerate(behavior_keys):
        raw_data[behavior_key] = (np.array(raw_data[behavior_key]))
        complete_raw_data[behavior_key] = (np.array(complete_raw_data[behavior_key]))
        plt.subplot(len(behavior_keys),2,2*i+1)
        plt.boxplot(raw_data[behavior_key], labels=[behavior_key], showmeans=True, meanline=True)
        plt.subplot(len(behavior_keys),2,2*i+2)
        plt.boxplot(complete_raw_data[behavior_key], labels=[behavior_key], showmeans=True, meanline=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-bf", "--behavior-files", help="TSV file paths", action='append')
    parser.add_argument("-bk", "--behavior-keys", help="keys to use for each TSV file", action="append")
    args = parser.parse_args()
    subjects, complete_subjects, raw_data, complete_raw_data = get_data(args.behavior_files, args.behavior_keys)
    draw_figure(args.behavior_keys, raw_data, complete_raw_data, autoscale=False)
    plt.show()
