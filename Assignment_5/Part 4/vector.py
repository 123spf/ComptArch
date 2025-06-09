# Script for Assignment 5, Part 2 and Part 5

import m5
from m5.objects import *

m5.util.addToPath("../../../configs")

from common.cores.arm import HPI

from learning_gem5.part1.caches import *

from common import SimpleOpts

# --- Set up command-line options ---

thispath = os.path.dirname(os.path.realpath(__file__))

default_binary_path = os.path.join(thispath, "FloatMM_scalar")


SimpleOpts.add_option(
    "--binary", nargs="?", default=default_binary_path, help="Binary to execute"
)

args = SimpleOpts.parse_args()

# --- Create the System ---
system = System() 

# Clock Domain
# As in simple-arm.py and two_level.py
system.clk_domain = SrcClockDomain() 
system.clk_domain.clock = "1GHz" 
system.clk_domain.voltage_domain = VoltageDomain() 

# Memory Setup
system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MiB")]

# --- Create the CPU ---

system.cpu = ArmMinorCPU() 

# --- Create the Cache Hierarchy ---

system.cpu.icache = L1ICache() 
system.cpu.dcache = L1DCache() 

# Connect L1 caches to the CPU
system.cpu.icache.connectCPU(system.cpu) 
system.cpu.dcache.connectCPU(system.cpu) 

# L2 Bus (Coherent Crossbar)
system.l2bus = L2XBar() 

# Connect L1 caches to the L2 Bus
system.cpu.icache.connectBus(system.l2bus) 
system.cpu.dcache.connectBus(system.l2bus) 

# L2 Cache
system.l2cache = L2Cache() 
system.l2cache.connectCPUSideBus(system.l2bus) 

# Memory Bus (connects L2 to main memory)
system.membus = SystemXBar() 

# Connect L2 cache to the Memory Bus
system.l2cache.connectMemSideBus(system.membus) 

# --- Interrupt Controller ---
system.cpu.createInterruptController()


# --- Main Memory ---
system.mem_ctrl = MemCtrl() 
system.mem_ctrl.dram = DDR3_1600_8x8() 
system.mem_ctrl.dram.range = system.mem_ranges[0] 
system.mem_ctrl.port = system.membus.mem_side_ports 

# System Port 
system.system_port = system.membus.cpu_side_ports 

# --- Workload Setup ---
# Using SEWorkload as in simple-arm.py and two_level.py
system.workload = SEWorkload.init_compatible(args.binary) 

process = Process() 
process.cmd = [args.binary] 
system.cpu.workload = process 
system.cpu.createThreads() 

# --- Simulation ---
root = Root(full_system=False, system=system) 
m5.instantiate() 

print("Beginning simulation!") 
exit_event = m5.simulate()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}") 
