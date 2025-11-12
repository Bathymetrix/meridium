# Author: Joel D. Simon <jdsimon@bathymetrix.com>
# Last modified: 12-Nov-2025
# Last tested: Python Python Python 3.12.0, Darwin Kernel Version 23.6.0

import os
import re
import math
from collections import defaultdict

LINE_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}).*?disconnected after\s*(\d+)\s*s",
    re.IGNORECASE
)

def find_cycle_files(root_dir):
    """Recursively yield paths to files ending with *CYCLE.h"""
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if fname.endswith("CYCLE.h"):
                yield os.path.join(dirpath, fname)

def parse_transmissions(files):
    """Parse each CYCLE.h file and sum transmission times by YYYY-MM"""
    totals = defaultdict(int)
    seen_timestamps = set()
    for f in files:
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as infile:
                for line in infile:
                    match = LINE_RE.search(line)
                    if match:
                        timestamp = match.group(1)
                        minutes = int(match.group(2)) / 60
                        third_minutes = math.ceil(minutes * 3) / 3
                        month = timestamp[:7]
                        if timestamp not in seen_timestamps:
                            totals[month] += third_minutes
                            seen_timestamps.add(timestamp)
        except Exception as e:
            print(f"Error reading {f}: {e}")
    return totals

def write_results(totals, output_file="rudics_minutes.txt"):
    """Write the summed results to a plain text file"""
    with open(output_file, "w") as out:
        out.write("  Month	 Minutes\n")
        for month in sorted(totals):
            third_minutes = math.ceil(totals[month] * 3 ) / 3
            out.write(f"{month}: {totals[month]:7.2f}\n")
    print(f"Wrote: {output_file}\n")


if __name__ == "__main__":
    # Write $MERMAID/processed_everyone/<float-name>/rudics_minutes.txt
    root_dir = os.environ.get("MERMAID")
    if root_dir is None:
        raise EnvironmentError("MERMAID environment variable not set.")

    processed_dir = os.path.join(root_dir, "processed_everyone")

    # Loop over all subdirectories
    for subdir_name in os.listdir(processed_dir):
        subdir_path = os.path.join(processed_dir, subdir_name)
        if subdir_name.startswith("."):
            continue
        if not os.path.isdir(subdir_path):
            continue
        print(f"Processing: {subdir_path}")

        # Find all CYCLE.h files in this subdir recursively
        cycle_files = list(find_cycle_files(subdir_path))

        # Parse transmissions
        totals = parse_transmissions(cycle_files)

        # Save output inside this subdir
        output_file = os.path.join(subdir_path, "rudics_minutes.txt")
        write_results(totals, output_file)
