import argparse
import os
import re
import subprocess
import sys


def parse_arguments():
    parser = argparse.ArgumentParser(description="Wrapper for arcasHLA genotype.")
    parser.add_argument("fastq1", type=str, help="Path to fastq file (single-end) or first fastq file (paired-end 1).")
    parser.add_argument("--fastq2", type=str, default=None, help="Path to second fastq file (paired-end 2), optional.")
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


def ensure_fastq_extension(filepath):
    if not filepath.endswith(".fastq.gz"):
        return f"{filepath}.fastq.gz"
    return filepath


def build_command(args):
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
    fastq1 = ensure_fastq_extension(args.fastq1)
    command.append(fastq1)

    if args.fastq2:
        # Paired-end
        fastq2 = ensure_fastq_extension(args.fastq2)
        command.append(fastq2)
    else:
        # Single-end
        command += ["--single", "--avg", str(args.avg), "--std", str(args.std)]

    return command


def execute_command(command):
    try:
        print(f"Start executing ArcasHLA with command: \n{' '.join(command)}")
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


def main():
    args = parse_arguments()
    # Adjust drop_iterations based on library layout
    if args.fastq2:
        # Paired-end, adjust if needed based on paired-end specific settings
        args.drop_iterations = 10  # Example adjustment, modify as needed
    command = build_command(args)
    execute_command(command)
    rename_output_files("/outputs/results/")


if __name__ == "__main__":
    main()
