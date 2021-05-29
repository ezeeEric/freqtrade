"""
Templates to setup analysis suite
"""

SLURM_JOB_TEMPLATE ="""\
#!/bin/bash
#SBATCH --time={time}
#SBATCH --cpus-per-task={cores}
#SBATCH --mem={memory}
#SBATCH --account={project}
#SBATCH --job-name={jobname}
#SBATCH --error={logsdir}/%x.e%A
#SBATCH --output={logsdir}/%x.o%A
#SBATCH --nodelist=cdr1643
#--gres=gpu:p100:1
#--gres=gpu:v100l:1

#export variables needed within Container environment - SINGULARITYENV_ affix needed
export SINGULARITYENV_SLURM_SUBMIT_DIR=${{SLURM_SUBMIT_DIR}}
export SINGULARITYENV_SLURM_JOB_NAME=${{SLURM_JOB_NAME}}
export SINGULARITYENV_SLURM_JOB_USER=${{SLURM_JOB_USER}}
export SINGULARITYENV_SLURM_JOB_ID=${{SLURM_JOB_ID}}
export SINGULARITYENV_HOSTNAME=${{HOSTNAME}}

export SINGULARITYENV_TMPDIR=/{local_scratch}/${{SLURM_JOB_USER}}/${{SLURM_JOB_ID}}
export SINGULARITYENV_LOGSDIR=${logsdir}
export SINGULARITYENV_OUTDIR=${outdir}

#execute (by setting up container)
export SINGULARITY_BINDPATH="$SFUSMLKITINPUTPATH,$SFUSMLKITOUTPUTPATH,$PWD"
module load python/3.6
module load singularity
singularity run /project/ctb-stelzer/bjager/public/singularity/containers/sfusmlkit-container.sif {runscript}
"""

setup_cedar="""
pwd; whoami; date; hostname -f; date -u
source setup.sh
"""
