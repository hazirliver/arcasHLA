import argparse
import os
import re
import subprocess
import sys


def print_directory_contents(path):
    for root, dirs, files in os.walk(path):
        level = root.replace(path, "").count(os.sep)
        indent = " " * 4 * (level)
        print("{}{}/".format(indent, os.path.basename(root)))
        subindent = " " * 4 * (level + 1)
        for f in files:
            print("{}{}".format(subindent, f))


def parse_arguments():
    parser = argparse.ArgumentParser(description="Wrapper for arcasHLA genotype.")
    parser.add_argument("bam", type=str, help="Path to bam file.")
    parser.add_argument("--genes", nargs="+",
                        default=["A", "B", "C", "DMA", "DMB", "DOA", "DOB", "DPA1", "DPB1", "DQA1", "DQB1", "DRA",
                                 "DRB1", "DRB3", "DRB5", "E", "F", "G", "H", "J", "K", "L"],
                        help="List of genes to analyze.")
    parser.add_argument("--population", default="prior", type=str, help="Population prior.")
    parser.add_argument("--min_count", default=75, type=int, help="Minimum read count.")
    parser.add_argument("--tolerance", default=1e-7, type=float, help="Tolerance for stopping.")
    parser.add_argument("--max_iterations", default=1000, type=int, help="Maximum number of iterations.")
    parser.add_argument("--drop_iterations", default=4, type=int,
                        help="Number of iterations to drop, adjust based on input type.")
    parser.add_argument("--drop_threshold", default=0.01, type=float, help="Drop threshold.")
    parser.add_argument("--zygosity_threshold", default=0.15, type=float, help="Zygosity threshold.")
    parser.add_argument("--threads", default=os.cpu_count(), type=int, help="Number of threads.")
    parser.add_argument("--avg", default=200, type=int, help="Average insert size for single-end.")
    parser.add_argument("--std", default=20, type=int, help="Standard deviation of insert size for single-end.")
    return parser.parse_args()


def ensure_bam_extension(filepath):
    if not filepath.endswith(".bam"):
        return f"{filepath}.bam"
    return filepath


def build_command_extract(args):
    command = ["arcasHLA", "extract"]
    command += ["--threads", str(args.threads),
                "--outdir", "/outputs/results/",
                "--log", "/outputs/results/sample.extract.log",
                "--verbose"]

    # Ensure the fastq files have the correct extension
    bam = ensure_bam_extension(args.bam)
    command.append(bam)

    return command


def get_extracted_fastq(bam) -> tuple[str, str]:
    filename = bam.split(".")[-2].split("/")[-1]
    return f"/outputs/results/{filename}.extracted.1.fq.gz", f"/outputs/results/{filename}.extracted.2.fq.gz"


def build_command_genotype(args):
    command = ["arcasHLA", "genotype"]
    genes = ",".join(args.genes)
    command += ["--genes", genes]
    command += ["--outdir", "/outputs/results/"]
    command += ["--population", args.population,
                "--min_count", str(args.min_count),
                "--tolerance", str(args.tolerance),
                "--max_iterations", str(args.max_iterations),
                "--drop_iterations", str(args.drop_iterations),
                "--drop_threshold", str(args.drop_threshold),
                "--zygosity_threshold", str(args.zygosity_threshold),
                "--threads", str(args.threads)]

    # Ensure the fastq files have the correct extension
    fq1, fq2 = get_extracted_fastq(args.bam)
    command.append(fq1)
    command.append(fq2)

    return command


def execute_command(command):
    try:

        print(f"Start executing with command: \n{' '.join(command)}")
        result = subprocess.run(command, shell=False, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Stderr: {result.stderr}", file=sys.stderr)


    except subprocess.CalledProcessError as e:
        print(f"Error executing arcasHLA: {e}", file=sys.stderr)
        sys.exit(1)


def rename_output_files(output_dir):
    prefix_pattern = re.compile(r"^[a-f0-9\-]+-([\w\-]+)(?:_[12])?\.(.*)$")

    for filename in os.listdir(output_dir):
        match = prefix_pattern.match(filename)
        if match:
            essential_part, extension = match.group(1), match.group(2)
            if "_" in essential_part:
                essential_part = essential_part.split("_")[0]
            new_name = f"{essential_part}.{extension}"
            original_path = os.path.join(output_dir, filename)
            new_path = os.path.join(output_dir, new_name)
            os.rename(original_path, new_path)
            print(f"Renamed {filename} to {new_name}")


def build_command_version(args):
    return ["samtools", "--version"]


def build_command_cp2tmp(args):
    os.makedirs("/tmp/bam_file/", exist_ok=True)
    fname = args.bam.split("/")[-1]
    command = ["cp", args.bam, f"/tmp/bam_file/{fname}"]
    args.bam = f"/tmp/bam_file/{fname}"
    return command


def main():
    print("Contents of '/inputs' folder:")
    print_directory_contents("/inputs")
    os.makedirs("/outputs/results/", exist_ok=True)
    args = parse_arguments()
    # Adjust drop_iterations based on library layout

    command_cp2tmp = build_command_cp2tmp(args)
    execute_command(command_cp2tmp)

    # command_index = build_command_version(args)
    # execute_command(command_index)

    command_extract = build_command_extract(args)
    execute_command(command_extract)

    print_directory_contents("/outputs/results/")

    command_genotype = build_command_genotype(args)
    execute_command(command_genotype)

    rename_output_files("/outputs/results/")


if __name__ == "__main__":
    main()
