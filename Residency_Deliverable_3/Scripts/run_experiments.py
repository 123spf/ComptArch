import os
import itertools
import argparse
import subprocess

# ===================================================================
# gem5 Simulation Automation Script (Python)
#
# ===================================================================

# --- Configuration Variables ---
GEM5_EXEC = "build/ALL/gem5.opt"
CONFIG_SCRIPT = "configs/learning_gem5/residency/arm_iotbench.py"
BASE_OUTDIR = "m5out_wearable_tests"

# --- Define parameter ranges ---

L1_SIZES = ["4KiB", "8KiB", "16KiB"]
L2_SIZES = ["0", "64KiB"]

ASSOCIATIVITIES = [2, 8]


DVFS_MODES = {
    "Passive":  {"freq": "50MHz", "volt": "0.8V"},
    "Baseline": {"freq": "64MHz", "volt": "0.9V"},
    "Active":   {"freq": "75MHz", "volt": "1.0V"},
    "Burst":    {"freq": "100MHz", "volt": "1.2V"}
#}
# Attempted these "optimal" DVFS modes first but quickly realized that only Optimal-Passive was appropriate.
#DVFS_MODES = {
 #   "Optimal-Passive": {"freq": "25MHz", "volt": "0.75V"},
  #  "Optimal-Active":  {"freq": "50MHz", "volt": "0.8V"},
   # "Optimal-Burst":   {"freq": "75MHz", "volt": "1.0V"}
#}

#Final Optimal DVFS, along with previous Optimal-Passive and first Passive now designated as Optimal-Burst
#DVFS_MODES = {
#    "Optimal-Active-New": {"freq": "35MHz", "volt": "0.77V"}
#}



# --- Helper Functions to Run Simulations ---

def run_gem5_command(command_list):
    """Executes a gem5 command and checks for errors."""
    print(f"Executing: {' '.join(command_list)}")
    # Using subprocess is more robust than os.system
    process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print("--- GEM5 FAILED ---")
        print(stderr.decode())
        print("---------------------")
    else:
        print("--- GEM5 SUCCEEDED ---")


def run_phase1a(workload_binary, workload_name):
    """Runs all cache size experiments (Phase 1a)."""
    print(f"\n--- Running Phase 1a: Cache Size Optimization for {workload_name.upper()} ---")
    fixed_assoc = 8
    fixed_freq = "64MHz"
    fixed_volt = "0.9V"

    for l1_size, l2_size in itertools.product(L1_SIZES, L2_SIZES):
        outdir = os.path.join(BASE_OUTDIR, f"{workload_name}_phase1a_l1_{l1_size}_l2_{l2_size}_assoc{fixed_assoc}")
        
        command = [
            GEM5_EXEC, 
            "-re", # redirect stdout and stderr
            f"--outdir={outdir}", CONFIG_SCRIPT,
            f"--binary={workload_binary}",
            f"--clk_freq={fixed_freq}", f"--voltage={fixed_volt}",
            f"--l1i_size={l1_size}", f"--l1d_size={l1_size}",
            f"--l2_size={l2_size}",
            f"--l1i_assoc={fixed_assoc}", f"--l1d_assoc={fixed_assoc}"
        ]
        run_gem5_command(command)

def run_phase1b(workload_binary, workload_name, l1_size, l2_size):
    """Runs cache associativity experiments (Phase 1b) on a chosen cache size."""
    print(f"\n--- Running Phase 1b: Associativity Tests for {workload_name.upper()} ---")
    print(f"    (Using optimal sizes: L1={l1_size}, L2={l2_size})")
    fixed_freq = "64MHz"
    fixed_volt = "0.9V"

    for assoc in ASSOCIATIVITIES:
        outdir = os.path.join(BASE_OUTDIR, f"{workload_name}_phase1b_l1_{l1_size}_l2_{l2_size}_assoc{assoc}")
        command = [
            GEM5_EXEC, 
            "-re",
            f"--outdir={outdir}", CONFIG_SCRIPT,
            f"--binary={workload_binary}",
            f"--clk_freq={fixed_freq}", f"--voltage={fixed_volt}",
            f"--l1i_size={l1_size}", f"--l1d_size={l1_size}",
            f"--l2_size={l2_size}",
            f"--l1i_assoc={assoc}", f"--l1d_assoc={assoc}"
        ]
        run_gem5_command(command)

def run_phase2(workload_binary, workload_name, l1_size, l2_size, assoc):
    """Runs DVFS experiments (Phase 2) on a final cache configuration."""
    print(f"\n--- Running Phase 2: DVFS Evaluation for {workload_name.upper()} ---")
    print(f"    (Using final config: L1={l1_size}, L2={l2_size}, Assoc={assoc})")

    for mode, params in DVFS_MODES.items():
        outdir = os.path.join(BASE_OUTDIR, f"{workload_name}_phase2_{mode}")
        command = [
            GEM5_EXEC, 
            "-re",
            f"--outdir={outdir}", CONFIG_SCRIPT,
            f"--binary={workload_binary}",
            f"--clk_freq={params['freq']}", f"--voltage={params['volt']}",
            f"--l1i_size={l1_size}", f"--l1d_size={l1_size}",
            f"--l2_size={l2_size}",
            f"--l1i_assoc={assoc}", f"--l1d_assoc={assoc}"
        ]
        run_gem5_command(command)

# --- Main script execution logic ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run gem5 experiments for the wearable device project.")
    
    parser.add_argument("--phase", required=True, choices=['1a', '1b', '2'])
    parser.add_argument("--workload", required=True, choices=['basic', 'advanced'])
    
    # Optional arguments needed for later phases
    parser.add_argument("--l1_size", default="16KiB", help="Optimal L1 size")
    parser.add_argument("--l2_size", default="0", help="Optimal L2 size")
    parser.add_argument("--assoc", default="8", help="Optimal associativity")

    args = parser.parse_args()

    # Set the binary path based on the chosen workload
    if args.workload == 'basic':
        binary_path = "configs/learning_gem5/IoTBench/iotbench-ARM-basic"
    else:
        binary_path = "configs/learning_gem5/IoTBench/iotbench-ARM-advanced"
    

    # Execute the requested phase
    if args.phase == '1a':
        run_phase1a(binary_path, args.workload)
    elif args.phase == '1b':
        run_phase1b(binary_path, args.workload, args.l1_size, args.l2_size)
    elif args.phase == '2':
        run_phase2(binary_path, args.workload, args.l1_size, args.l2_size, args.assoc)

    print("\nScript finished for the requested phase.")

