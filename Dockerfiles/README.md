Dockerfiles
===========

Move each Dockerfile to the parent directory and rename to 'Dockerfile' before
building.

Currently each file is named based on a reasonable name for the docker image
that would be built from the file.

NOTES:
 - arv-cli
   - Installs the Arvados Command Line Interface, the Arvados python SDK, and Arvados CWL runner.
   - Does not need any flags to build (other than -t for tagging)
   - Image built will require environment definitions for the Arvados token and host (which are available under "Current Token" in the web interface)
 - arv-pysdk-datalad
   - Installs the Arvados python SDK and the Arvados CWL runner
   - Building requires the --build-arg definitions of python_sdk_version and cwl_runner_version, which are in the header of the file. Also requires the file apt.arvados.org.list to be in the parent directory
   - Image built will require environment definitions for the Arvados token and host (which are available under "Current Token" in the web interface)
 - datalad
   - installs Datalad
   - Does not need any flags to build (other than -t for tagging)
   - expects a volume to be mounted at "/data" for running and will enter into scripts/find_subjects_neuro_data_lite.py

Files in unusableDockerfiles are simply documentation of an attempt to build a docker image that could run arv-mount (as a more direct route of uploading data). It appears that running a fuse mount in a docker image requires certain dependencies of the host, which I was unable to figure out.
