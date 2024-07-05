#!/bin/bash
# Copyright (c) 2021 Johnny on Flame.
# 
# Provided under the MIT license for the PortMaster packaging system
# See LICENSE for more details. This is free software.

# Docs:
#   This script provides the $TASKSET variable when taskset is present, and all
# sanity checks were passed, otherwise, $TASKSET is left empty.
#   The $TASKSET parameter uses `taskset` to pin your legacy port to the fastest
# available cores in the system in order to work around any issues arising from
# possibly unfortunate core scheduling on older kernels.
# 
# Usage:
# source $controlfolder/tasksetter.sh
# $TASKSET ./game

get_taskset () {
	MAXMHZ_PERF=0
	PERF_CORES=
	TASKSET=

	# Check if we have taskset installed
	if ! command -v taskset &> /dev/null
	then
		echo "taskset not found, bailing..."
		return
	fi

	# Query cpu info
	cpus="$(lscpu -p=CPU,MAXMHZ)"
	if [[ $? != 0 ]]; then
		echo "lscpu failure, bailing... (TASKSET won't be available)"
		return
	fi

	# Iterate over the known cpu cores
	while IFS=, read -r CPU MAXMHZ; do
		if [[ "${CPU::1}" == '#' ]]; then
			continue
		fi

		# Remember the largest seen cpu frequency
		if [[ $MAXMHZ > $MAXMHZ_PERF ]]; then
			MAXMHZ_PERF=$MAXMHZ
			PERF_CORES=$CPU
		elif [[ $MAXMHZ == $MAXMHZ_PERF ]]; then
			PERF_CORES="$PERF_CORES,$CPU"
		fi
	done <<< "$cpus"

	# Do final sanity check
	if [[ "x${PERF_CORES}" == x || ${MAXMHZ_PERF} == 0 ]]; then
		echo "PERFCORES or MAXMHZ were not initialized somehow, bailing... (TASKSET won't be available)"
		return
	fi

	TASKSET="taskset -c ${PERF_CORES} "
	echo "p-cores: $PERF_CORES (@${MAXMHZ_PERF}mhz)"
}

get_taskset
echo "cmd: $TASKSET"
