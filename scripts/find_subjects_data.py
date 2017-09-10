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

def get_data(paths_and_keys):
    path_and_key = []
    for i, inp in enumerate(paths_and_keys):
        if i % 2 == 0:
            path_and_key.append([inp])
        else:
            path_and_key[int(i/2)].append(inp)
    subjects = {}
    behavior_keys = []
    for path, behavior_key in path_and_key:
        subjects = find_subjects_with_reported_behavior(subjects, behavior_key, path)
        behavior_keys.append(behavior_key)
    num_subjects_with_all_data = 0
    complete_subjects = {}
    raw_data = {behavior_key:[] for behavior_key in behavior_keys}
    complete_raw_data = {behavior_key:[] for behavior_key in behavior_keys}
    for subject in subjects:
        for behavior_key in behavior_keys:
            if behavior_key in subjects[subject]:
                raw_data[behavior_key].append(subjects[subject][behavior_key])
        if len(subjects[subject]) == len(path_and_key):
            num_subjects_with_all_data += 1
            complete_subjects[subject] = subjects[subject]
            for behavior_key in behavior_keys:
                complete_raw_data[behavior_key].append(subjects[subject][behavior_key])
    print("%i subjects have data in all given files" % num_subjects_with_all_data)
    return subjects, complete_subjects, raw_data, complete_raw_data, behavior_keys

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
    parser.add_argument("behavior", help="At least 2 arguments required. First is the \
        file path to the TSV file. Second is the key name found in the first \
        row of the tsv file",
        nargs='+', metavar="File paths and behavior keys")
    args = parser.parse_args()
    assert len(args.behavior) % 2 == 0, "File paths and behavior keys must be tuples"
    subjects, complete_subjects, raw_data, complete_raw_data, behavior_keys = get_data(args.behavior)
    draw_figure(behavior_keys, raw_data, complete_raw_data, autoscale=False)
    plt.show()
