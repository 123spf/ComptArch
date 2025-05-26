import m5
from m5.objects import *

# gem5 standard library components
from gem5.components.boards.x86_board import X86Board
from gem5.components.memory.multi_channel import DualChannelDDR4_2400
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.components.processors.simple_processor import SimpleProcessor # Using SimpleProcessor for the detailed run
from gem5.simulate.simulator import Simulator
from gem5.simulate.exit_event import ExitEvent
from gem5.resources.resource import obtain_resource, CheckpointResource

# Using the standard library's PrivateL1SharedL2CacheHierarchy
from gem5.components.cachehierarchies.classic.private_l1_shared_l2_cache_hierarchy import (
    PrivateL1SharedL2CacheHierarchy,
)
print("Restore Script: Using PrivateL1SharedL2CacheHierarchy from gem5.components.")

# --- Script Configuration ---

checkpoint_to_restore_path = "timing_settled_checkpoint"


# --- Component Setup ---
# Cache Hierarchy
cache_hierarchy = PrivateL1SharedL2CacheHierarchy(
    l1d_size="32KiB",    
    l1i_size="32KiB",    
    l2_size="256KiB",    
    l1d_assoc=8,         
    l1i_assoc=8,         
    l2_assoc=16         
)
print(f"Restore Script: Using {cache_hierarchy.__class__.__name__}.")

# Memory System: Size must match the checkpointed system.
mem_checkpointed_size = "3GB"
memory = DualChannelDDR4_2400(size=mem_checkpointed_size)
print(f"Restore Script: Memory {mem_checkpointed_size} configured (must match checkpoint).")

# Processor: TimingSimpleCPU. num_cores must match checkpoint.
num_checkpointed_cores = 1
processor = SimpleProcessor(
    cpu_type=CPUTypes.TIMING,
    isa=ISA.X86,
    num_cores=num_checkpointed_cores
)
# The actual CPU object is processor.cores[0]
print(f"Restore Script: Using {processor.cores[0].__class__.__name__} as the detailed CPU.")

# Board
board = X86Board(
    clk_freq="3GHz", # Should match clock frequency of the checkpointed system
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)


# --- Set Workload for Restore ---

# Obtain the original workload resource to get its kernel and disk image components
# This is the same workload that was used to create the checkpoint.
workload_name_for_restore = "x86-ubuntu-24.04-npb-sp-s"
print(f"Restore Script: Obtaining base workload info for resource '{workload_name_for_restore}' to correctly set up board for checkpoint restore.")
try:
    main_workload_meta_resource = obtain_resource(workload_name_for_restore)
except Exception as e:
    print(f"Error obtaining main workload resource '{workload_name_for_restore}': {e}")
    exit(f"Cannot proceed without main workload information for restore: {workload_name_for_restore}")

# Extract the kernel and disk image resource objects, and kernel_args
# using the get_parameters() method as figured out from resource.py
workload_params = main_workload_meta_resource.get_parameters()
try:
    actual_kernel_resource = workload_params["kernel"]
    actual_disk_image_resource = workload_params["disk_image"]
    kernel_args_from_resource = workload_params.get("kernel_args", board.get_default_kernel_args())

    print(f"Restore Script: Using KernelResource: {actual_kernel_resource.get_id()} for board setup.")
    print(f"Restore Script: Using DiskImageResource: {actual_disk_image_resource.get_id()} for board setup.")
    print(f"Restore Script: Using Kernel Args for board setup: {kernel_args_from_resource}")
except KeyError as e:
    print(f"Error accessing 'kernel', 'disk_image', or 'kernel_args' from WorkloadResource parameters: Missing key {e}")
    print(f"Available parameters in workload '{workload_name_for_restore}' are: {list(workload_params.keys())}")
    exit("Cannot extract necessary components from WorkloadResource for restore setup.")

# Set the kernel, disk, and checkpoint for the board.
# This initializes the board in FS mode and tells it to load from the checkpoint.
board.set_kernel_disk_workload(
    kernel=actual_kernel_resource,
    disk_image=actual_disk_image_resource,
    checkpoint=CheckpointResource(checkpoint_to_restore_path), # Pass the CheckpointResource
    kernel_args=kernel_args_from_resource
)
print(f"Restore Script: Board workload configured to restore from checkpoint: {checkpoint_to_restore_path}")


# --- ROI Exit Event Handlers ---
def handle_roi_workbegin():
    print("RESTORE_SCRIPT: ROI Workbegin detected (resuming from checkpoint).")
    print("RESTORE_SCRIPT: Resetting stats for ROI.")
    m5.stats.reset()
    yield False # Continue simulation into ROI

def handle_roi_workend():
    print("RESTORE_SCRIPT: ROI Workend detected.")
    print("RESTORE_SCRIPT: Dumping stats for ROI.")
    m5.stats.dump()
    print("RESTORE_SCRIPT: Exiting simulation after ROI.")
    yield True # Exit simulation

def handle_generic_exit_restore():
    print("RESTORE_SCRIPT: Generic m5 exit or unexpected end post-restore.")
    m5.stats.dump() # Dump stats just in case
    yield True

# --- Simulator Setup ---
simulator = Simulator(
    board=board,
  
    on_exit_event={
        ExitEvent.WORKBEGIN: handle_roi_workbegin(),
        ExitEvent.WORKEND: handle_roi_workend(),
        ExitEvent.EXIT: handle_generic_exit_restore(),
    },
    # After restoring, expect WORKBEGIN, then WORKEND from the benchmark
    expected_execution_order = [ExitEvent.WORKBEGIN, ExitEvent.WORKEND]
)


# --- Run Simulation ---
print(f"RESTORE_SCRIPT: Starting simulation, restoring from checkpoint: {checkpoint_to_restore_path}")
print(f"RESTORE_SCRIPT: Detailed CPU: {processor.cores[0].__class__.__name__}")
print(f"RESTORE_SCRIPT: Cache Hierarchy: {cache_hierarchy.__class__.__name__}")

simulator.run() # Simulation runs until an exit event handler yields True

print("RESTORE_SCRIPT: Simulation complete.")
