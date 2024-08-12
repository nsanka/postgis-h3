#! /usr/bin/python3
# https://fictional-bassoon-1w293vv.pages.github.io/dev/usage/contributing.html

import argparse
import logging
import random
import re
import subprocess
from shutil import which
from time import sleep

try:
    import coloredlogs

    coloredlogs.install(level="INFO")
except ImportError:
    logging.basicConfig(level="INFO")

SBATCH_TEMPLATE = """sbatch --parsable << EOF
#!/bin/bash
#SBATCH --container-image {image}
#SBATCH --container-mount-home
#SBATCH --partition {partition}
#SBATCH --gres gpu:{n_gpus}
#SBATCH --cpus-per-task {n_cpus}
#SBATCH --container-writable
#SBATCH --container-mounts /data_zfs/hf_cache:/data_zfs/hf_cache,/data_lustre:/data_lustre,/data_lustre/user_data/nsanka/postgis_storage:/var/lib/postgresql/data
#SBATCH --time=0-12:00:00
#SBATCH --job-name {job_name}

# print hostname
hostname -i
export POSTGRES_DB=postgres
export POSTGRES_USER=nsanka
export POSTGRES_PASSWORD=changeme
export PGPORT={port}
mkdir /run/postgresql && chown postgres: /run/postgresql

/usr/lib/postgresql/15/bin/pg_ctl initdb -D /var/lib/postgresql/data
/usr/lib/postgresql/15/bin/pg_ctl start -l logfile -D /var/lib/postgresql/data
tail -f logfile

EOF
"""


def get_cli_output(command: str) -> str:
    """Get a string output from the command line"""
    output = subprocess.run(command, stdout=subprocess.PIPE, shell=True, check=True)
    return output.stdout.decode("utf-8").strip()


def main(partition, n_gpus, n_cpus, image):
    """Main entry point for launch an LLM server as slurm sbatch job"""

    if which("sbatch") is None:
        logging.critical("You are not in a Slurm cluster")
        raise RuntimeError("You are not in a Slurm cluster")

    # Additional setup
    port = random.randint(40000, 45000)
    logging.info("PostGIS port %d", port)
    job_name = "postgis-server-aic"

    sbatch_cmd = SBATCH_TEMPLATE.format(
        image=image,
        partition=partition,
        n_gpus=n_gpus,
        n_cpus=n_cpus,
        job_name=job_name,
        port=port,
    )

    job_id = int(get_cli_output(sbatch_cmd))
    logging.info("Job queued with id %d", job_id)

    # Get output file
    job_info = get_cli_output(f"scontrol show jobid {job_id} -o")
    stdout_file = re.findall(r"StdOut=([\/\w\-\.]+)", job_info)[0]

    # Wait for the job to become running
    while True:
        job_info = get_cli_output(f"scontrol show jobid {job_id} -o")
        job_state = re.findall(r"JobState=(\w+)", job_info)[0]
        if job_state == "RUNNING":
            logging.info("Job %d is running", job_id)
            break
        elif job_state in ["CANCELLED", "COMPLETED", "FAILED"]:
            logging.critical("Job %d has %s.", job_id, job_state.lower())
            raise RuntimeError(f"Job {job_id} has {job_state.lower()}.")
        else:
            logging.info("Job %d is pending, waiting to start...", job_id)
            sleep(10)

    logging.info("Waiting for server to spawn...")
    n_read_lines = 0

    try:
        while True:
            with open(stdout_file, "r", encoding="utf-8") as fp:
                lines = fp.readlines()[n_read_lines:]
                if len(lines) == 0:
                    continue
                for line in lines:
                    logging.info(line.strip())
                n_read_lines += len(lines)
            sleep(10)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch a postgis server")
    parser.add_argument("--partition", type=str, default="std", help="Slurm partition")
    parser.add_argument("--n-gpus", type=int, default=0, help="Number of GPUs")
    parser.add_argument("--n-cpus", type=int, default=4, help="Number of CPU cores")
    parser.add_argument(
        "--image",
        type=str,
        default="/shared/home/nsanka/Workspace/GitHub/Stellantis-ADX/pppa/postgis-h3.sqsh",
        help="Docker image",
    )

    args = parser.parse_args()

    main(**vars(args))
