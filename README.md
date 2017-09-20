# predicting-depression

Project to downloading the resting-state fMRI data and behavioral data from MPI-Leipzig Mind-Brain-Body dataset, preprocess the MRI data through NiPype, building regressors on the MRI and behavioral data to predict depressive behaviors, and predicting depressive behaviors from resting-state fMRI data: either by separating the MPI-Leipzig data into test-training groups or by accessing the Brain Genomics Superstruct project, which has the NEO behavioral data for its subjects.

Ultimately, we hope this project will be used for even more: specifically, expanding to different types of neuroimaging data (sMRI and DTI).

## Theoretical Motivation

20% of all people are expected to fulfill the criteria for major depressive disorder (MDD) at some point in their lifetime, and MDD is the second leading contributor to chronic disease burden, yet 50% of patients do not respond or remiss to their first treatment (Benazzi 2006, Gartlehner *et al* 2012, Otte *et al* 2016).

We hope to build a model with a known confidence from over 100 subjects that can predict depression severity given the resting-state fMRI of a subject. We predict the connectivity patterns weighted by the model will implicate regions and tracts affected by and necessary for a depressive phenotype, furthering research into the etiology of depression.

## Research Design

1. Choose a dataset with at least 100 subjects who cover a range of depressive severity.
   - The MPI-Leipzig dataset has ~6 moderately depressed subjects measured using the Beck Depression Inventory (BDI). All subjects in the lower three-quartiles  are not considered to be depressed. [BDI](https://www.commondataelements.ninds.nih.gov/doc/noc/beck_depression_inventory_noc_link.pdf)
   - This pattern is also observed using the HADS-D score to measure depression.
2. Find subjects which have behavioral data of BDI, HADS-D, and NEO-N, and do not fail quality control testing (as run by mriqc).
3. Preprocess the subjects fulfilling the above requirements.
4. Build a connectome for each subject using nilearn.
5. Separate subjects into a large training set and a small test set. (Note, we may choose to use the GSP dataset as our test set.)
6. Build 3 cognitive-based predictive models (CPM) to predict depressive
   phenotypes: BDI, HADS-D, and NEO-N.
   - For each edge in all subjects connectomes, correlate the strength of that edge with the phenotype score. Edges that are most strongly related to behavior in the positive and negative directions are retained for model building. Use cross-validation to ensure reliability of the positive network and the negative network.
   - Build a linear model relating each individual’s positive network strength (i.e., the sum of the connections in their positive network) and negative network strength (i.e., the sum of the connections in their negative network) to their behavioral score.
7. Check the validity of the model against the test set. Predictive power is assessed by correlating predicted and observed behavioral scores across the group.

CPM will be based on the research done by Shen *et al*, 2017.

All computing is currently planned to run using cwl-runner on Arvados, which provides a reproducible computing infrastructure.

## Statistical Analysis

The statistical analysis involved in this project will involve correlating the strength of each edge with the phenotype score, model-fitting the CPM, and using cross-validation.

Building a CPM uses a form of linear regression, such as Pearson's correlation, Spearman's correlation, or robust regression. We plan to use Spearman's rank correlation instead of Pearson's correlation, since depressive severity does not follow a normal distribution in our data. We will use a significance threshold of P=0.01 to choose significantly positive or negative edges in the CPM.

We will fit the CPM model using a least squares polynomial fit (numpy.polyfit)

We shall evaluate the mean squared error and the true prediction correlation to to evaluate the prediction performance of the CPM model.

## Code Development

 - [x] Dataset exploration (scripts/find_subject_data.py, scripts/find_subjects_neuro_data.py, and scripts/download_subjects_neuro_data_to_arvados)
 - [ ] QC (cwl/mriqc.cwl)
 - [ ] Preprocessing (scripts/preprocess_subjects.py)
 - [ ] Building a connectome
 - [ ] Building a CPM
 - [ ] Evaluating the prediction performace of the CPM


# MRI Data Basics

sguthrie has written a Jupyter Notebook that summarizes her current working knowledge of the basics of MRI data and which data are available in the MPI-Leipzig dataset. This is a work-in-progress. A non-interactive view of the page may be found [here](https://github.com/sguthrie/predicting-depression/blob/master/MRI%20Data%20Basics%20and%20the%20MPI-Leipzig%20Dataset.ipynb).

# Getting to know the MPI-Leipzig Mind-Brain-Body Dataset

We provide a Jupyter Notebook allowing users to investigate what range of behavioral data is available from the MPI-Leipzig dataset. A non-interactive view of the page may be found using [nbviewer](https://nbviewer.jupyter.org/github/sguthrie/predicting-depression/blob/master/MPI-LeipzigDataset.ipynb).


# Uploading your chosen dataset to Arvados

Once you have chosen a set of behavioral data that have an appropriate range and number, you will probably want to actually get the imaging data associated with them. sguthrie has chosen to upload the data to a cloud server running [Arvados](https://doc.arvados.org/), an open-source computing system which enables large data storage and reproducible computing (disclosure: sguthrie worked at Curoverse, which maintained and built Arvados).


The script `download_subjects_neuro_data_to_arvados.py` will install a datalad dataset, query over behavioral data and filter subjects who only have that data stored, get the imaging data for each subject, and upload that data to a Collection in an Arvados project (one Collection per subject). It does this in such a way that only one subject's imaging data is stored on the user's system at a time, avoiding possible out of space errors. It requires a system with the Arvados python SDK and datalad installed.

## Building the system (docker image)

### Option 1: Using Dockerhub

Pull the pre-built image from Dockerhub:

`$ docker pull sguthrie/arv-pysdk-datalad`

### Option 2: Build image from source

1. Move `apt.arvados.org.list` and `arv-pysdk-datalad` from the directory `Dockerfiles` to its parent directory.
2. Rename `arv-pysdk-datalad` to `Dockerfile`.
3. In `predicting-depression`, build the image:

   `predicting-depression $ docker build -t <image-tag> --build-arg python_sdk_version=<apt-get version to install> --build-arg cwl_runner_version=<apt-get version to install> .`

## Running the system and uploading data

> **It is highly suggested that you run the following in a screen**

Run your image interactively (Yes, it is theoretically possible to build the image such that it runs non-interactively, it just hasn't been done; if you care strongly, create an issue). You will need to specify environment variables for Arvados tokens, which grant permissions to upload and interact with data. These may be found after you sign up in an Arvados cluster by choosing `Current Token` under the drop-down.

`$ docker run -it --rm -e ARVADOS_API_TOKEN=<token> -e ARVADOS_API_HOST=<host> <image-tag> \bin\bash`

Once inside the container, you can run `download_subjects_neuro_data_to_arvados.py`. The below example will upload all subjects that have BDI, HADS-D, and NEO-N scores, using only one core. It will take about 4 hours.

>** WARNING!**
> The Arvados SDK is only python2.7 compatible! Currently, all scripts in use are both 2.7 and 3 compatible, but `download_subjects_neuro_data_to_arvados.py` must be run in python2.


`$ python scripts/download_subjects_neuro_data_to_arvados.py --get-data -bf phenotype/BDI.tsv -bk BDI_summary_sum -bf phenotype/HADS.tsv -bk HADS-D_summary_sum -bf phenotype/NEO.tsv -bk NEO_N <project_uuid> /home/crunch ///openfmri/ds000221`


# References

Benazzi F (2006). Various forms of depression. **Dialogues Clin. Neurosci.** 8, 151-161.

Gartlehner G, Thaler K, Hill S, *et al* (2012). How should primary care doctors select which
antidepressants to administer? **Curr. Psychiatry Rep.** 14, 360-369.

Otte C, Gold SM, Pennix BW, *et al* (2016). Major depressive disorder. **Nature Reviews.** 2, 1-20.

Shen X, Finn ES, Scheinost D, *et al* (2017). Using connectome-based predictive modeling to predict individual behavior from brain connectivity. **Nature Protocols** 12, 506-518.
