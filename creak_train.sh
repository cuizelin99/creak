#!/bin/bash
# Stampede system.
#
# This script requests one core (out of 16) on one node. The job
# will have access to all the memory in the node.  Note that this
# job will be charged as if all 16 cores were requested.
#-----------------------------------------------------------------

#SBATCH -J DOWNLOAD_EMBED             # Job name
#SBATCH -o /work/06782/ysu707/maverick2/DPR/%j.out       # Specify stdout output file (%j expands to jobId)
#SBATCH -e /work/06782/ysu707/maverick2/DPR/%j.err       # stderr; skip to combine stdout and stderr
#SBATCH -p gtx                   # Queue name: gtx or v100 or p100 -- check availability using "sinfo" command
#SBATCH -N 1                     # Total number of nodes requested (16 cores/node)
#SBATCH -n 1                     # Total number of tasks
#SBATCH -t 4:00:00              # Run time (hh:mm:ss)

#SBATCH -A CS388      # Specify allocation to charge against

# Load any necessary modules (these are examples)
# Loading modules in the script ensures a consistent environment.
module load python3
module load cuda

# Launch jobs
source /work/06782/ysu707/maverick2/DPR/bin/activate   # Activate your virtual env here.
cd /work/06782/ysu707/maverick2/DPR     # Move to your working dir.

# Training a baseline model from scratch
python dense_retriever.py \
        model_file=/work/06782/ysu707/maverick2/DPR/downloads/checkpoint/retriever/single/nq/bert-base-encoder.cp \
        qa_dataset=creak_train  \
        ctx_datatsets=[dpr_wiki] \
        encoded_ctx_files=[\"/work/06782/ysu707/maverick2/DPR/downloads/data/retriever_results/nq/single-adv-hn/wikipedia_passages_*.pkl\"] \
        out_file=/work/06782/ysu707/maverick2/DPR/output/output.json
