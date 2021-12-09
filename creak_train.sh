#!/bin/bash

#SBATCH -J dpr     # Job name
#SBATCH -o dpr.o%j # Name of stdout output file
#SBATCH -e dpr.e%j # Name of stderr error file
#SBATCH -p rtx                 # Queue (partition) name
#SBATCH -A CCR20015
#SBATCH -N 2                   # Total # of nodes (must be 1 for serial)
#SBATCH -n 1                   # Total # of mpi tasks (should be 1 for serial)
#SBATCH -t 4:00:00            # Run time (hh:mm:ss)


# Launch jobs
source /work/06885/zc3968/frontera/DPR/bin/activate   # Activate your virtual env here.
cd /work/06885/zc3968/frontera/DPR     # Move to your working dir.

# Training a baseline model from scratch
python3 dense_retriever.py \
        model_file=/work/06885/zc3968/frontera/DPR/downloads/checkpoint/retriever/single/nq/bert-base-encoder.cp \
        qa_dataset=creak_train  \
        ctx_datatsets=[dpr_wiki] \
        encoded_ctx_files=[\"/work/06885/zc3968/frontera/DPR/downloads/data/retriever_results/nq/single-adv-hn/wikipedia_passages_*.pkl\"] \
        out_file=/work/06885/zc3968/frontera/DPR/output/output.json
