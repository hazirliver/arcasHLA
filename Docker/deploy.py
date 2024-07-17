import argparse
import datetime
import os
import subprocess
import sys
from pathlib import Path

REPO_URL = "028257207274.dkr.ecr.us-east-1.amazonaws.com/deconv"

DEFAULT_SSH_KEY_PATH = Path.home() / ".ssh" / "id_rsa"
AWS_REGION = "us-east-1"
AWS_ACCOUNT_ID = "028257207274"

def aws_ecr_login():
    login_command = (f"aws ecr get-login-password "
                     f"--region {AWS_REGION} | "
                     f"docker login "
                     f"--username AWS "
                     f"--password-stdin {AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com")
    subprocess.run(login_command, shell=True, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--ssh-key", default=str(DEFAULT_SSH_KEY_PATH),
                        help=f"Path to ssh key. If missed - will use system default: '{DEFAULT_SSH_KEY_PATH}'")
    parser.add_argument("-b", "--branch", default="master", help="Git branch name to clone repo")
    parser.add_argument("-i", "--image", default="osrp")
    parser.add_argument("-bo", "--build-only", action="store_true")
    parser.add_argument("-t", "--tag", default="osrp_arcashla_cwl-0.1.3-bam-input")
    parser.add_argument("-f", "--dockerfile", default="Dockerfile", help="Name of the Dockerfile to use")
    args = parser.parse_args()

    branch = args.branch
    ssh_key = Path(args.ssh_key).read_text()
    dockerfile = args.dockerfile

    tagged_image = f"{args.image}:{args.tag}"


    print(f"{tagged_image}: Building using {dockerfile} ...")
    subprocess.run(["docker", "build", "-t", tagged_image, ".", "-f", dockerfile,
                    "--build-arg", f"branch={branch}", "--build-arg", f"ssh_key={ssh_key}", "--build-arg", f"build_date={datetime.datetime.now()}"], check=False)


    if args.build_only:
        sys.exit()

    aws_ecr_login()

    repo_tag = f"{REPO_URL}/{tagged_image}"
    subprocess.run(["docker", "image", "tag", tagged_image, repo_tag], check=False)
    subprocess.run(["docker", "image", "push", repo_tag], check=False)
