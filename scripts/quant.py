#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------------
#   quant.py: genotypes from extracted chromosome 6 reads.
# -------------------------------------------------------------------------------

# -------------------------------------------------------------------------------
#   This file is part of arcasHLA.
#
#   arcasHLA is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   arcasHLA is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with arcasHLA.  If not, see <https://www.gnu.org/licenses/>.
# -------------------------------------------------------------------------------

import argparse
import json
import pickle
from argparse import RawTextHelpFormatter
from collections import defaultdict

import pandas as pd

from arcas_utilities import *

# -------------------------------------------------------------------------------

__version__ = "0.4.0"
__date__ = "2022-01-27"

# -------------------------------------------------------------------------------
rootDir = os.path.dirname(os.path.realpath(__file__)) + "/../"

parameters_json = rootDir + "dat/info/parameters.json"


# -------------------------------------------------------------------------------
def arg_check_files(parser, arg):
    for file in arg.split():
        if not os.path.isfile(file):
            parser.error("The file %s does not exist." % file)
        elif not (
                file.endswith("alignment.p") or file.endswith(".fq.gz") or file.endswith(".fastq.gz") or file.endswith(
                ".tsv") or file.endswith(".json")):
            parser.error("The format of %s is invalid." % file)
        return arg


if __name__ == "__main__":

    # with open(parameters, 'rb') as file:
    #    genes, populations, databases = pickle.load(file)
    with open(parameters_json, "r") as file:
        genes, populations, _ = json.load(file)
        genes = set(genes)
        populations = set(populations)

    parser = argparse.ArgumentParser(prog="arcasHLA quant",
                                     usage="%(prog)s [options] FASTQs",
                                     add_help=False,
                                     formatter_class=RawTextHelpFormatter)

    parser.add_argument("file",
                        help="list of fastq files",
                        nargs="*",
                        type=lambda x: arg_check_files(parser, x))

    parser.add_argument("-h",
                        "--help",
                        action="help",
                        help="show this help message and exit\n\n",
                        default=argparse.SUPPRESS)

    parser.add_argument("--sample",
                        help="sample name",
                        type=str,
                        default=None)

    parser.add_argument("--ref",
                        type=str,
                        help='arcasHLA quant_ref path (e.g. "/path/to/ref/sample")\n  ',
                        default=None,
                        metavar="")

    parser.add_argument("-o",
                        "--outdir",
                        type=str,
                        help="out directory\n\n",
                        default="./",
                        metavar="")

    parser.add_argument("--temp",
                        type=str,
                        help="temp directory\n\n",
                        default="/tmp/",
                        metavar="")

    parser.add_argument("--keep_files",
                        action="count",
                        help="keep intermediate files\n\n",
                        default=False)

    parser.add_argument("--single",
                        action="store_true",
                        help="Include flag if single-end reads. Default is paired-end.\n\n",
                        default=False)

    parser.add_argument("-l",
                        "--avg",
                        type=int,
                        help="Estimated average fragment length " +
                             "for single-end reads\n  default: 200\n\n",
                        default=200)

    parser.add_argument("-s",
                        "--std",
                        type=int,
                        help="Estimated standard deviation of fragment length " +
                             "for single-end reads\n  default: 20\n\n",
                        default=20)

    parser.add_argument("--LOH",
                        action="store_true",
                        help="Include flag for estimated loss of heterozygosity. " +
                             "Must provide purity and ploidy estimates.\n\n",
                        default=False)

    parser.add_argument("--purity",
                        type=float,
                        help="Estimated purity of sample\n  default: 1.0\n\n",
                        default=1.0)

    parser.add_argument("--ploidy",
                        type=int,
                        help="Estimated ploidy of sample\n  default: 2.0\n\n",
                        default=2.0)

    parser.add_argument("-t",
                        "--threads",
                        type=str,
                        default="1",
                        metavar="")

    parser.add_argument("-v",
                        "--verbose",
                        action="count",
                        default=False)

    args = parser.parse_args()

    paired = not args.single

    if args.sample == None:
        sample = os.path.basename(args.file[0]).split(".")[0]
    else:
        sample = args.sample

    outdir = check_path(args.outdir)
    temp = create_temp(args.temp)

    indv_idx = args.ref + ".idx"
    indv_p = args.ref + ".p"
    indv_abundance = outdir + sample + ".quant.tsv"
    allele_results_json = outdir + sample + ".quant.alleles.json"
    gene_results_json = outdir + sample + ".quant.genes.json"
    allele_results_tsv = outdir + sample + ".quant.alleles.tsv"
    gene_results_tsv = outdir + sample + ".quant.genes.tsv"
    loh_results_tsv = outdir + sample + ".quant.loh.tsv"

    with open(indv_p, "rb") as file:
        genes, genotype, hla_idx, allele_idx, lengths = pickle.load(file)

    idx_allele = defaultdict(set)
    for idx, gene in allele_idx.items():
        idx_allele[gene].add(idx)

    if args.file[0].endswith(".fq.gz") or args.file[0].endswith(".fastq.gz"):

        command = ["kallisto quant", "-i", indv_idx, "-o", temp, "-t", args.threads]

        if args.single:
            command.extend(["--single -l", str(args.avg), "-s", str(args.std)])

        command.extend(args.file)

        output = run_command(command, "[quant] Quantifying with Kallisto: ").stderr.decode()

        if args.verbose:
            print(output)

        total_reads = re.findall("(?<=processed ).+(?= reads,)", output)[0]
        total_reads = int(re.sub(",", "", total_reads))
        aligned_reads = re.findall("(?<=reads, ).+(?= reads pseudoaligned)", output)[0]
        aligned_reads = int(re.sub(",", "", aligned_reads))

        run_command(["mv", temp + "/abundance.tsv", indv_abundance])
        kallisto_results = pd.read_csv(indv_abundance, sep="\t")

    else:
        with open(args.file[1], "r") as file:
            previous_results = json.load(file)

        # total_reads = previous_results['total_count']
        # aligned_reads = previous_results['aligned_reads']

        kallisto_results = pd.read_csv(args.file[0], sep="\t")

    idx_allele = defaultdict(set)
    hla_indices = set()
    for idx, gene in allele_idx.items():
        if gene[:-1] in genes:
            idx_allele[gene].add(idx)
            hla_indices.add(int(idx))

    lengths = defaultdict(float)
    counts = defaultdict(float)
    tpm = defaultdict(float)
    for gene, indices in idx_allele.items():
        for idx in indices:
            counts[gene] += kallisto_results.loc[int(idx)]["est_counts"]
            lengths[gene] += kallisto_results.loc[int(idx)]["length"]
            tpm[gene] += kallisto_results.loc[int(idx)]["tpm"]

    gene_results = {gene: defaultdict(int) for gene in genes}

    allele_results = {gene: defaultdict(float) for gene in genes}

    total_hla_count = 0
    for allele_id, allele in genotype.items():
        allele_results[allele_id[:-1]]["allele" + allele_id[-1]] = allele
        total_hla_count += counts[allele_id]

    for gene, allele_ids in genes.items():
        for allele_id in set(allele_ids):
            gene_results[gene]["count"] += round(counts[allele_id])
            gene_results[gene]["tpm"] += round(tpm[allele_id])
            if counts[allele_id]:
                gene_results[gene]["abundance"] += counts[allele_id] / total_hla_count

            allele_results[gene]["allele" + allele_id[-1] + "_count"] = round(counts[allele_id])
            allele_results[gene]["allele" + allele_id[-1] + "_tpm"] = round(tpm[allele_id])
    for gene, allele_ids in genes.items():
        for allele_id in set(allele_ids):
            baf = allele_results[gene]["allele1_count"] / (
                        allele_results[gene]["allele1_count"] + allele_results[gene]["allele2_count"])
            allele_results[gene]["baf"] = round(min(baf, 1 - baf), 2)
    for gene in genes:
        gene_results[gene]["abundance"] = str(round(gene_results[gene]["abundance"] * 100, 2)) + "%"

    df = pd.DataFrame(allele_results).T
    df.index.names = ["gene"]
    try:
        df = df[["allele1", "allele2", "allele1_count", "allele2_count", "allele1_tpm", "allele2_tpm", "baf"]]
    except:
        df = df[["allele1", "allele1_count", "allele1_tpm"]]
    df.to_csv(allele_results_tsv, sep="\t")

    df = pd.DataFrame(gene_results).T
    df.index.names = ["gene"]
    df = df[["count", "tpm", "abundance"]]
    df.to_csv(gene_results_tsv, sep="\t")

    with open(allele_results_json, "w") as file:
        json.dump(allele_results, file)

    with open(gene_results_json, "w") as file:
        json.dump(gene_results, file)

    if not args.keep_files: run_command(["rm -rf", temp])

    # LOH functionality
    if (args.LOH):
        corrections_columns = []

        for gene in genes:
            corrections_columns.append(gene + "_CN_1")
            corrections_columns.append(gene + "_CN_2")
            corrections_columns.append(gene + "_LOSS")
            corrections_columns.append(gene + "_lost")

        corrections_df = pd.DataFrame(columns=corrections_columns)

        for gene in genes:
            baf1 = allele_results[gene]["allele1_count"] / (allele_results[gene]["allele1_count"] + \
                                                            allele_results[gene]["allele2_count"])
            baf2 = 1 - baf1

            correction1 = (2 * baf1 * (1 + args.purity * (args.ploidy - 2) / 2) + args.purity - 1) / (args.purity)
            correction2 = (2 * baf2 * (1 + args.purity * (args.ploidy - 2) / 2) + args.purity - 1) / (args.purity)

            if correction1 < correction2:
                minor = correction1
                major = correction2
            else:
                minor = correction2
                major = correction1

            corrections_df.at[0, gene + "_CN_1"] = correction1
            corrections_df.at[0, gene + "_CN_2"] = correction2

            if (correction1 < 0.5) or (correction2 < 0.5):
                corrections_df.at[0, gene + "_LOSS"] = True

                if (correction1 < 0.5) and (correction2 < 0.5):
                    corrections_df.at[0, gene + "_lost"] = ",".join(allele_results[gene][["allele1", \
                                                                                          "allele2"]].tolist())

                elif (correction1 < 0.5):
                    corrections_df.at[0, gene + "_lost"] = allele_results[gene]["allele1"]

                else:
                    corrections_df.at[0, gene + "_lost"] = allele_results[gene]["allele2"]

            else:
                corrections_df.at[0, gene + "_LOSS"] = False
                corrections_df.at[0, gene + "_lost"] = "none"

        corrections_df.to_csv(loh_results_tsv, sep="\t", index=False)

# -----------------------------------------------------------------------------
