import m5
from m5.objects import *
import os

# Create a system
system = System()

# Set up the clock domain
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"  #
system.clk_domain.voltage_domain = VoltageDomain() #

# Set up the memory system
system.mem_mode = "timing"  # Use timing models for memory accesses
system.mem_ranges = [AddrRange("512MiB")]  # Define the address range for the memory

# Create an ARM MinorCPU
system.cpu = ArmMinorCPU()

# Create an interrupt controller for the CPU
system.cpu.createInterruptController() #

# Create a memory bus
system.membus = SystemXBar() #

# Connect the CPU cache ports to the memory bus
# ArmMinorCPU has icache_port and dcache_port for connecting to L1 caches or the memory bus
system.cpu.icache_port = system.membus.cpu_side_ports #
system.cpu.dcache_port = system.membus.cpu_side_ports #

# Create a memory controller and connect it to the bus
system.mem_ctrl = MemCtrl() #
system.mem_ctrl.dram = DDR3_1600_8x8()  # Define the type of DRAM
system.mem_ctrl.dram.range = system.mem_ranges[0] #
system.mem_ctrl.port = system.membus.mem_side_ports #

# Connect the system port for functional access
system.system_port = system.membus.cpu_side_ports #

# --- Set up the workload ---

binary_path = "/home/user/IoTBench/iotbench-ARM-HealthTest"


system.workload = SEWorkload.init_compatible(binary_path) #

# Create a process
process = Process() #
process.cmd = [binary_path] #
system.cpu.workload = process #
system.cpu.createThreads() #

# --- Instantiate the system and start simulation ---
root = Root(full_system=False, system=system) #
m5.instantiate()

print("Beginning simulation!") #
exit_event = m5.simulate()

print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}") #
