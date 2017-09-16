cwlVersion: v1.0
class: CommandLineTool

hints:
  DockerRequirement:
    dockerPull: poldracklab/mriqc:0.9.8-1

baseCommand: /usr/local/miniconda/bin/mriqc
arguments:
  out_dir:
    value: $(runtime.outdir)
    inputBinding: {position: 2}
inputs:
  inp_dir:
    type: Directory
    inputBinding: {position: 1}
  participants:
    type: string[]
    inputBinding:
      position: 3
      prefix: participants

outputs:
  reports:
    type: Directory
    outputBinding: reports/ #items will be .html files
  derivatives:
    type: Directory
    outputBinding: derivatives/ # items will be .json
  logs:
    type: Directory
    outputBinding: logs/
    
