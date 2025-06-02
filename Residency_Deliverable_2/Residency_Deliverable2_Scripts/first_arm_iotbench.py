import m5
from m5.objects import *
import os
import optparse 

# --- Add command-line option for the binary ---
parser = optparse.OptionParser() 

parser.add_option( 
    "-b", "--binary",
    default="/home/user/IoTBench/iotbench-ARM-basic",
    help="Path to the ARM binary to execute"
)

(options, args) = parser.parse_args() 

# Create a system
system = System()

# Set up the clock domain
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

# Set up the memory system
system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MiB")]

# Create an ARM MinorCPU
system.cpu = ArmMinorCPU()
system.cpu.createInterruptController()

# Create a memory bus
system.membus = SystemXBar()

# Connect the CPU cache ports to the memory bus
system.cpu.icache_port = system.membus.cpu_side_ports
system.cpu.dcache_port = system.membus.cpu_side_ports

# Create a memory controller and connect it to the bus
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# Connect the system port for functional access
system.system_port = system.membus.cpu_side_ports

# --- Set up the workload ---
# Use the binary path from command-line options
binary_path = options.binary 


system.workload = SEWorkload.init_compatible(binary_path)

# Create a process
process = Process()
process.cmd = [binary_path] # Command is a list of strings
system.cpu.workload = process
system.cpu.createThreads()

# --- Instantiate the system and start simulation ---
root = Root(full_system=False, system=system)
m5.instantiate()

print(f"Beginning simulation for: {binary_path}") 

exit_event = m5.simulate()

print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
