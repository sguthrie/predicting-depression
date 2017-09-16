"""
Shamelessly copied from https://miykael.github.io/nipype-beginner-s-guide/firstLevel.html

Meant to preprocess the fMRI neuroimaging data. QC will be done
with mriqc

"""
import csv
import json
import argparse

from nipype.interfaces.afni import Despike
from nipype.interfaces.freesurfer import (BBRegister, ApplyVolTransform,
                                          Binarize, MRIConvert, FSCommand)
from nipype.interfaces.spm import (SliceTiming, Realign, Smooth, Level1Design,
                                   EstimateModel, EstimateContrast)
from nipype.interfaces.utility import Function, IdentityInterface
from nipype.interfaces.io import FreeSurferSource, SelectFiles, DataSink
from nipype.algorithms.rapidart import ArtifactDetect
from nipype.algorithms.misc import TSNR, Gunzip
from nipype.algorithms.modelgen import SpecifySPMModel
from nipype.pipeline.engine import Workflow, Node, MapNode

#We need MATLAB and FreeSurfer interfaces to run correctly
# MATLAB - Specify path to current SPM and the MATLAB's default mode
from nipype.interfaces.matlab import MatlabCommand
MatlabCommand.set_default_paths('/usr/local/MATLAB/R2014a/toolbox/spm12')
MatlabCommand.set_default_matlab_cmd("matlab -nodesktop -nosplash")

# FreeSurfer - Specify the location of the freesurfer folder
fs_dir = '~/nipype_tutorial/freesurfer'
FSCommand.set_default_subjects_dir(fs_dir)

def get_subject_list(subject_file):
    subject_list = []
    with open(subject_file, 'r') as tsv:
        tsv = csv.DictReader(tsv, delimiter='\t')
        for subject in tsv:
            subject_list.append(subject["participant_id"])
    return subject_list

def fwhm_choice(s):
    if s == 'mriqc':
        return s
    elif s == 'default'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset-dir", help="Directory containing data")
    parser.add_argument("subject-list", help="tsv file containing the subjects to preprocess. The subjects must be labeled `participant_id`")
    parser.add_argument("output-dir", help="Directory to place result in")
    parser.add_argument("working-dir", help="Working directory")
    #Add fwhm choice group
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--mriqc-fwhm', help='Choose full width at half max paramemter based on the average in the mriqc json file')
    group.add_argument("--manual-fwhm", type=float, help="Full width at Half Maximum value source")
    args = parser.parse_args()

    #location of dataset folder
    experiment_dir = args.dataset_dir
    #list of subject identifiers
    subject_list = get_subject_list(args.subject_list)
    output_dir = args.output_dir
    working_dir = args.working_dir
    #NOTE: it appears that the number of slices, the TR,
    # and possibly the FWHM might vary even within a subject
    # Thus, this particular pipeline might need to be altered
    # for each .nii.gz file

    # number of slices in volume
    # Can be found by opening the .json file of the fMRI .nii file and counting
    # the elements of "SliceTiming"
    number_of_slices = 40
    # time repetition of volume
    # Can be found by opening the .json file of the fMRI .nii file (Value of
    # "RepetitionTime")
    TR = 2.0
    # size of FWHM in mm
    # fwhm is one of the parameters output in the json file of mriqc
    if args.manual_fwhm:
        fwhm_size = args.manual_fwhm
    elif args.mriqc_fwhm:
        with open(args.mriqc_fwhm) as mriqc_out:
            d = json.load(mriqc_out)
            fwhm_size = float(d['fwhm_avg'])
    assert 'fwhm_size' in locals(), "fwhm_size must be defined"

    ######################################################
    #      Create all nodes needed for Preprocessing
    ######################################################
    # Despike - Removes 'spikes' from the 3D+time input dataset
    despike = MapNode(Despike(outputtype='NIFTI'),
        name="despike", iterfield=['in_file'])

    # Slicetiming - correct for slice wise acquisition
    # MIGHT not be required for rsFMRI, especially because it appears Multiband
    # sequencing was used (https://en.wikibooks.org/wiki/Neuroimaging_Data_Processing/Slice_Timing)
    #interleaved_order = range(1,number_of_slices+1,2) + range(2,number_of_slices+1,2)
    #TODO interleaved_order needs to be defined by opening the .json file of the
    # fMRI .nii file (Value of "SliceTiming")
    #ref_slice: Typically either the first time-point of the TR, i.e. the time
    # the first slice of the volume was acquired, or the middle time-point,
    # i.e. the slice of the volume that was acquired at TA/2, are chosen as
    # reference slices. Choosing the first time-point has the advantage of being
    # straightforward, as e.g. GLM analyses can then be performed using the
    # volume onset as time information. Using the middle time-point might be
    # more accurate since less interpolation is needed (the maximum time 
    # difference being TA/2 versus a full TA) but it has to be accounted for
    # when modelling the signal/event onsets.
    #sliceTiming = Node(SliceTiming(num_slices=number_of_slices,
    #                           time_repetition=TR,
    #                           time_acquisition=TR-TR/number_of_slices,
    #                           slice_order=interleaved_order,
    #                           ref_slice=2),
    #               name="sliceTiming")

    # Realign - correct for motion
    realign = Node(Realign(register_to_mean=True), name="realign")

    # TSNR - remove polynomials 2nd order
    tsnr = MapNode(TSNR(regress_poly=2), name='tsnr', iterfield=['in_file'])

    # Artifact Detection - determine which of the images in the functional series
    #   are outliers. This is based on deviation in intensity or movement.
    art = Node(ArtifactDetect(norm_threshold=1,
                              zintensity_threshold=3,
                              mask_type='file',
                              parameter_source='SPM',
                              use_differences=[True, False]),
                name="art")

# Gunzip - unzip functional
gunzip = MapNode(Gunzip(), name="gunzip", iterfield=['in_file'])

# Smooth - to smooth the images with a given kernel
smooth = Node(Smooth(fwhm=fwhm_size),
              name="smooth")

# FreeSurferSource - Data grabber specific for FreeSurfer data
fssource = Node(FreeSurferSource(subjects_dir=fs_dir),
                run_without_submitting=True,
                name='fssource')

# BBRegister - coregister a volume to the Freesurfer anatomical
bbregister = Node(BBRegister(init='header',
                             contrast_type='t2',
                             out_fsl_file=True),
                  name='bbregister')

# Volume Transformation - transform the brainmask into functional space
applyVolTrans = Node(ApplyVolTransform(inverse=True),
                     name='applyVolTrans')

# Binarize -  binarize and dilate an image to create a brainmask
binarize = Node(Binarize(min=0.5,
                         dilate=1,
                         out_type='nii'),
                name='binarize')
