import m5
from m5.objects import *

# gem5 standard library components
from gem5.components.boards.x86_board import X86Board
from gem5.components.memory.multi_channel import DualChannelDDR4_2400
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.components.processors.simple_switchable_processor import SimpleSwitchableProcessor
from gem5.resources.resource import obtain_resource, CheckpointResource 
from gem5.simulate.simulator import Simulator
from gem5.simulate.exit_event import ExitEvent
from gem5.components.cachehierarchies.classic.no_cache import NoCache 

# --- Script Configuration ---
# Path for the checkpoint directory
checkpoint_dir_name = "timing_settled_checkpoint"


# Flags to manage state
checkpoint_taken_flag = False



# --- Component Setup ---
cache_hierarchy = NoCache() # For KVM boot phase
print(f"KVM_SWITCH_CHECKPOINT: Using {cache_hierarchy.__class__.__name__} for initial KVM boot.")

mem_configured_size = "3GB"
memory = DualChannelDDR4_2400(size=mem_configured_size)
print(f"KVM_SWITCH_CHECKPOINT: Memory {mem_configured_size} configured.")

processor = SimpleSwitchableProcessor(
    starting_core_type=CPUTypes.KVM,
    switch_core_type=CPUTypes.TIMING, # Detailed CPU to switch to
    isa=ISA.X86,
    num_cores=1
)
print(f"KVM_SWITCH_CHECKPOINT: SimpleSwitchableProcessor configured (KVM -> TIMING).")

for core_wrapper in processor.start: # Configure KVM cores
    kvm_actual_core = core_wrapper.core
    kvm_actual_core.usePerf = False
    print(f"KVM_SWITCH_CHECKPOINT: Configured KVM core {kvm_actual_core.cpu_id} to usePerf = False.")

board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy, # NoCache for KVM phase
)

workload_name = "x86-ubuntu-24.04-npb-sp-s"
print(f"KVM_SWITCH_CHECKPOINT: Attempting to obtain workload resource: {workload_name}")
try:
    workload_resource = obtain_resource(workload_name)
except Exception as e:
    print(f"Error obtaining resource '{workload_name}': {e}")
    exit(f"Cannot proceed without workload resource: {workload_name}")

board.set_workload(workload_resource) # Uses the workload's internal setup
print(f"KVM_SWITCH_CHECKPOINT: Successfully set workload using: {workload_resource.get_id()}")




# --- Revised Exit Event Handlers ---

def os_boot_and_cpu_switch_generator():
    """
    Handles the OS boot m5 exit events and performs the CPU switch.
    """
    global simulator # Ensure simulator is accessible if not already global/passed

    print("KVM_SWITCH_CHECKPOINT: Handler waiting for 1st OS m5 exit (kernel boot)...")
    yield False  # Consume the 1st ExitEvent.EXIT

    print("KVM_SWITCH_CHECKPOINT: 1st OS m5 exit received. Waiting for 2nd OS m5 exit (after_boot.sh / systemd stable)...")
    yield False  # Consume the 2nd ExitEvent.EXIT

    # After the second OS m5 exit, the OS should be stable. Switch to TimingSimpleCPU.
    print("KVM_SWITCH_CHECKPOINT: 2nd OS m5 exit received. Switching CPUs from KVM to TIMING...")
    processor.switch() # Perform the CPU switch
    current_core_simobject = processor.get_cores()[0].core
    print(f"KVM_SWITCH_CHECKPOINT: CPUs switched. Current CPU type: {current_core_simobject.__class__.__name__}")

    print("KVM_SWITCH_CHECKPOINT: Resetting stats after CPU switch (TimingCPU now active).")
    m5.stats.reset()
    
    print("KVM_SWITCH_CHECKPOINT: OS boot and CPU switch complete. Waiting for benchmark WORKBEGIN to take checkpoint.")
    # This generator is done with its role for ExitEvent.EXIT.
    # The simulation continues, now on TimingSimpleCPU, until WORKBEGIN or another exit.
    yield False # Allow simulation to continue to the next phase (benchmark execution)


def handle_benchmark_workbegin_and_checkpoint():
    """
    Handles the WORKBEGIN event from the NPB benchmark.
    Takes the checkpoint and then exits the simulation.
    """
    global checkpoint_taken_flag
    global simulator # Ensure simulator is accessible

    print("KVM_SWITCH_CHECKPOINT: Benchmark WORKBEGIN detected on TimingSimpleCPU.")
    
    if not checkpoint_taken_flag:
        print(f"KVM_SWITCH_CHECKPOINT: Taking checkpoint in directory: '{checkpoint_dir_name}'")
        simulator.save_checkpoint(checkpoint_dir_name)
        checkpoint_taken_flag = True
        print("KVM_SWITCH_CHECKPOINT: Checkpoint saved successfully.")
    else:
        print("KVM_SWITCH_CHECKPOINT: Checkpoint was already attempted/taken.")
        
    print("KVM_SWITCH_CHECKPOINT: Exiting simulation after taking checkpoint at WORKBEGIN.")
    yield True # Terminate simulation

def handle_unexpected_workend_or_final_exit():
    """
    Handles WORKEND or any further EXIT if reached before desired checkpoint, or after.
    """
    global checkpoint_taken_flag
    if not checkpoint_taken_flag:
        print("KVM_SWITCH_CHECKPOINT: WARNING - Reached WORKEND or final OS EXIT before checkpoint at WORKBEGIN. Checkpoint not taken as intended.")
    else:
        print("KVM_SWITCH_CHECKPOINT: Reached WORKEND or final OS EXIT after checkpoint was taken. This is fine.")
    print("KVM_SWITCH_CHECKPOINT: Terminating simulation.")
    yield True


# --- Simulator Setup ---
simulator = Simulator(
    board=board,
    on_exit_event={
        ExitEvent.EXIT: os_boot_and_cpu_switch_generator(),
        ExitEvent.WORKBEGIN: handle_benchmark_workbegin_and_checkpoint(),
        ExitEvent.WORKEND: handle_unexpected_workend_or_final_exit(), # Safety handler
    },
    # The expected critical sequence for this script:
    # 1. OS boot 1st stage done
    # 2. OS boot 2nd stage done (CPU switch happens here)
    # 3. Benchmark ROI begins (WORKBEGIN - checkpoint happens here, then script exits)
    expected_execution_order=[
        ExitEvent.EXIT,
        ExitEvent.EXIT,
        ExitEvent.WORKBEGIN,
    ]
)





# --- Run Simulation ---

print("KVM_SWITCH_CHECKPOINT: Starting Full System simulation for switch, settle, and checkpoint.")
if hasattr(processor, 'start') and processor.start: # 'start' gives the list of SimpleCore wrappers for the initial cores
    actual_kvm_core_object = processor.start[0].core # .core gives the actual KvmCPU SimObject
    starting_cpu_class_name = actual_kvm_core_object.__class__.__name__

    # Access the list of "switch-to" SimpleCore wrappers via _switchable_cores and _switch_key
    # These attributes are set by SimpleSwitchableProcessor
    if hasattr(processor, '_switchable_cores') and \
       hasattr(processor, '_switch_key') and \
       processor._switch_key in processor._switchable_cores:
        
        switch_to_core_wrappers = processor._switchable_cores[processor._switch_key]
        if switch_to_core_wrappers:
            switch_to_actual_core_object = switch_to_core_wrappers[0].core
            switch_to_cpu_class_name = switch_to_actual_core_object.__class__.__name__
            print(f"KVM_SWITCH_CHECKPOINT: Processor: {processor.__class__.__name__}, "
                  f"starting with {starting_cpu_class_name}, and will switch to {switch_to_cpu_class_name}.")
        else:
            print(f"KVM_SWITCH_CHECKPOINT: Processor: {processor.__class__.__name__}, "
                  f"starting with {starting_cpu_class_name}, but 'switch' core list is empty.")
    else:
        print(f"KVM_SWITCH_CHECKPOINT: Processor: {processor.__class__.__name__}, "
              f"starting with {starting_cpu_class_name}, 'switch' core details not available directly.")

simulator.run()

# --- Post-Simulation Summary ---
if checkpoint_taken_flag:
    print(f"KVM_SWITCH_CHECKPOINT: Checkpoint process complete. Checkpoint in an output subdirectory named '{checkpoint_dir_name}'.")
else:
    print("KVM_SWITCH_CHECKPOINT: Simulation finished. Expected event sequence for checkpoint may not have completed.")
    print("Please check simout.txt for the sequence of exit events.")
