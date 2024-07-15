FROM mambaorg/micromamba:jammy

# Set the working directory in the container
WORKDIR /app
USER root
# Install dependencies including wget and pigz for data processing
RUN apt-get update && \
    apt-get install -y git curl pigz wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER $MAMBA_USER
# Clone the specific repository
ARG build_date
RUN git clone https://github.com/hazirliver/arcasHLA.git

#COPY --chown=$MAMBA_USER:$MAMBA_USER mamba_env/env.yml /tmp/env.yml

RUN micromamba install -y -n base -f /app/arcasHLA/environment.yml && \
    micromamba clean --all --yes

#RUN mkdir /root/app

ARG MAMBA_DOCKERFILE_ACTIVATE=1

# Prepare the IMGTHLA directory and download the HLA database
RUN mkdir -p /app/arcasHLA/dat/IMGTHLA && \
    cd /app/arcasHLA/dat/IMGTHLA && \
    wget -m -nH --cut-dirs=5 --exclude-directories=/pub/databases/ipd/imgt/hla/previous_releases ftp://ftp.ebi.ac.uk/pub/databases/ipd/imgt/hla/

# Argument for the commit hash to be used in arcasHLA reference command
ARG COMMIT_HASH=e4fd1e3

# Use the commit hash as an environment variable
ENV COMMIT_HASH_ENV=${COMMIT_HASH}

# Run the arcasHLA reference command using the commit hash environment variable
RUN cd /app/arcasHLA && \
    ./arcasHLA reference --commit ${COMMIT_HASH_ENV}

# Add arcasHLA to the PATH
ENV PATH=/app/arcasHLA/:$PATH

USER root

RUN mkdir -p /outputs
RUN chmod -R 777 /outputs
RUN chown -hR $MAMBA_USER:$MAMBA_USER /outputs

RUN DEBIAN_FRONTEND=noninteractive apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y sudo aptitude
RUN sudo adduser $MAMBA_USER sudo
RUN sudo sh -c "echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers"
RUN sudo usermod -a -G sudo $MAMBA_USER
RUN apt-get clean

USER $MAMBA_USER

# Copy the arcashla.py script into the container
COPY arcashla.py /app/arcasHLA/arcashla.py
COPY entry.sh /app/entry.sh


# Set the entrypoint to use the conda environment and run the script
ENTRYPOINT ["stdbuf", "-i0", "-o0", "-e0", "/bin/bash", "/app/entry.sh"]
