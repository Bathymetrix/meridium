# Author: Joel D. Simon <jdsimon@bathymetrix.com>
# Last modified: 13-Nov-2025
# Last tested: Python Python Python 3.12.0, Darwin Kernel Version 23.6.0

import os
import re
import math
from collections import defaultdict

conn_re = re.compile(
    r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}).*?connected in\s*(\d+)\s*s",
    re.IGNORECASE
)
disc_re = re.compile(
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
    """Parse all CYCLE.h files and sum transmission times by YYYY-MM"""
    totals = defaultdict(float)
    timestamps = set()
    for f in files:
        current_connection = None
        with open(f, "r", encoding="utf-8", errors="ignore") as infile:
            for line in infile:
                conn = conn_re.search(line)
                disc = disc_re.search(line)

                ts = None
                if conn:
                    ts = conn.group(1)
                elif disc:
                    ts = disc.group(1)
                if ts in timestamps:
                    continue
                timestamps.add(ts)

                # always replace with latest connect before next disconnect
                # (do we want to do it this way???)
                if conn:
                    current_connection = conn
                elif current_connection and disc:
                    conn_time = int(current_connection.group(2))
                    disc_time = int(disc.group(2))
                    minutes = (disc_time - conn_time) / 60
                    third_minutes = math.ceil(minutes * 3) / 3
                    month = disc.group(1)[:7]
                    totals[month] += third_minutes
                    connected = False

    return totals

def write_results(totals, output_file="rudics_minutes.txt"):
    """Write the summed results to a plain text file"""
    with open(output_file, "w") as out:
        out.write("  Month	 Minutes\n")
        for month in sorted(totals):
            out.write(f"{month}: {totals[month]:7.2f}\n")
    print(f"Wrote: {output_file}\n")

if __name__ == "__main__":
    root_dir = os.environ.get("MERMAID")
    if root_dir is None:
        raise EnvironmentError("MERMAID environment variable not set.")

    processed_dir = os.path.join(root_dir, "processed_everyone")
    for subdir_name in os.listdir(processed_dir):
        subdir_path = os.path.join(processed_dir, subdir_name)
        if subdir_name.startswith("."):
            continue
        if not os.path.isdir(subdir_path):
            continue

        print(f"Processing: {subdir_path}")
        cycle_files = list(find_cycle_files(subdir_path))
        totals = parse_transmissions(cycle_files)
        output_file = os.path.join(subdir_path, "rudics_minutes.txt")
        write_results(totals, output_file)
