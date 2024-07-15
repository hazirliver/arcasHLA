#!/bin/bash
#set -xu
set -uxo pipefail

export PATH=/opt/conda/bin:$PATH

OUTDIR="${OUTPUTS_DIR}" #"${TMPDIR}/output/"
OUT_PKG_DIR="${OUTDIR}/output_package"

cd "$HOME"
sudo -n mkdir -p "${OUTDIR}"
sudo -n mkdir -p "${OUTDIR}/logs"
sudo -n mkdir -p "${OUTDIR}/results"
sudo -n chown -hR "$(whoami)":"$(whoami)" "${OUTDIR}"
sudo -n chmod -R ug+rwx $OUTDIR
sudo -n chown "$(whoami)":"$(whoami)" "${OUTPUTS_DIR}"
sudo -n chmod -R 777"${OUTPUTS_DIR}"
sudo -n chown -hR "$(whoami)":"$(whoami)" "${TMPDIR}"
sudo -n chmod -R 777 "${TMPDIR}"
mkdir -p "${OUT_PKG_DIR}"
echo "All arguments to entry script: $@"
echo "$@" >> "${OUTDIR}/logs/cmdline.log"
echo "$*" >> "${OUTDIR}/logs/cmdline_ast.log"
proctype=$(cat /proc/cpuinfo)
meminfo=$(cat /proc/meminfo)
echo "Launching entrypoint script on a machine with the following capabilities: ${proctype} ${meminfo}" | tee -a "${OUTDIR}/logs/machine.log"
echo "Launching Python script passing it all arguments"
( (/opt/conda/bin/python /app/arcasHLA/arcashla.py "$@" | tee -a "${OUTDIR}/logs/stdout.log" ) 3>&1 1>&2 2>&3 | tee -a "${OUTDIR}/logs/stderr.log" ) #&> all.log
exitcode="$?"
if [[ "$exitcode" -ne 0 ]]; then
	echo "Python script finished with FAILURE"
fi
echo "Finished Python script"
ls -lahR "${OUT_PKG_DIR}" > "${OUTDIR}/logs/output_package_ls.log"
echo "Creating output package"
pushd "${OUT_PKG_DIR}"
#tar -cvf "${OUTDIR}/package.tar" .
popd
#zstd -z -6 --adapt -T0 "${OUTDIR}/package.tar" -o "${OUTDIR}/package.tar.zst"
echo "Compression finished"
#rm -rf "${OUTDIR}/package.tar"
ls -lahR "${OUTDIR}" | tee -a "${OUTDIR}/logs/output_ls.log"
echo "DONE"
echo $exitcode
exit 0
