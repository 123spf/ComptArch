# arm_iotbench.py

import m5
from m5.objects import *
import os
import optparse

# --- Define Cache Classes ---

class MyL1Cache(Cache):
    # Defaults based on Caches.py
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20

    def __init__(self, size, assoc):
        super(MyL1Cache, self).__init__()
        self.size = size
        self.assoc = assoc

    def connectBus(self, bus):
        self.mem_side = bus.cpu_side_ports

    def connectCPU(self, cpu_port):
        self.cpu_side = cpu_port

class MyL1ICache(MyL1Cache):
    is_read_only = True 
    writeback_clean = True 

    def __init__(self, size, assoc):
        super(MyL1ICache, self).__init__(size, assoc)

class MyL1DCache(MyL1Cache):
    def __init__(self, size, assoc):
        super(MyL1DCache, self).__init__(size, assoc)

class MyL2Cache(Cache):
    # Defaults based on Caches.py
    tag_latency = 20
    data_latency = 20
    response_latency = 20
    mshrs = 20
    tgts_per_mshr = 12
    write_buffers = 8 

    def __init__(self, size, assoc):
        super(MyL2Cache, self).__init__()
        self.size = size
        self.assoc = assoc

    def connectCPUSideBus(self, bus):
        self.cpu_side = bus.mem_side_ports

    def connectMemSideBus(self, bus):
        self.mem_side = bus.cpu_side_ports

# --- Command Line Options ---
parser = optparse.OptionParser()

parser.add_option(
    "-b", "--binary",
    default="configs/learning_gem5/IoTBench/iotbench-ARM-basic", 
    help="Path to the ARM binary to execute"
)
parser.add_option("--l1i_size", default="16KiB", help="L1 instruction cache size")
parser.add_option("--l1i_assoc", type="int", default=8, help="L1 instruction cache associativity")
parser.add_option("--l1d_size", default="16KiB", help="L1 data cache size")
parser.add_option("--l1d_assoc", type="int", default=8, help="L1 data cache associativity")
parser.add_option("--l2_size", default="0", help="L2 cache size (0 for no L2)")
parser.add_option("--l2_assoc", type="int", default=16, help="L2 cache associativity")


parser.add_option("--clk_freq", default="50MHz", help="CPU clock frequency for DVFS")
parser.add_option("--voltage", default="0.8V", help="CPU voltage for DVFS")

parser.add_option("--cache_line_size", default="64", help="cache line size")

(options, args) = parser.parse_args()

# --- System Setup ---
system = System()

system.clk_domain = SrcClockDomain()
system.clk_domain.voltage_domain = VoltageDomain() 

system.clk_domain.clock = options.clk_freq
system.clk_domain.voltage_domain.voltage = options.voltage # Set the voltage

system.mem_mode = "timing" 
system.mem_ranges = [AddrRange("512MiB")]
system.cache_line_size = options.cache_line_size   

# --- CPU ---
system.cpu = ArmMinorCPU() 
system.cpu.createInterruptController() 


# --- Memory System ---
system.membus = SystemXBar() 

# --- Cache Hierarchy ---
# L1 Caches
system.l1i_cache = MyL1ICache(options.l1i_size, options.l1i_assoc)
system.l1d_cache = MyL1DCache(options.l1d_size, options.l1d_assoc)

# Connect L1 caches to CPU
system.l1i_cache.connectCPU(system.cpu.icache_port)
system.l1d_cache.connectCPU(system.cpu.dcache_port)

# L2 Cache and Bus (optional)
has_l2_cache = True
if options.l2_size == "0":
    has_l2_cache = False

if has_l2_cache:
    system.l2bus = L2XBar()
    system.l1i_cache.connectBus(system.l2bus)
    system.l1d_cache.connectBus(system.l2bus)

    system.l2_cache = MyL2Cache(options.l2_size, options.l2_assoc)
    system.l2_cache.connectCPUSideBus(system.l2bus)
    system.l2_cache.connectMemSideBus(system.membus) # Connect L2 to main memory bus

else:
    # Connect L1s directly to main memory bus if no L2
    system.l1i_cache.connectBus(system.membus)
    system.l1d_cache.connectBus(system.membus)



# Connect system port for functional access (if needed by L1s if no L2, or L2)
system.system_port = system.membus.cpu_side_ports

# Memory Controller
system.mem_ctrl = MemCtrl()
# Instantiate LPDDR5 and override its device_size
system.mem_ctrl.dram = LPDDR5_5500_1x16_BG_BL16(device_size = str(system.mem_ranges[0].size()))
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports


# --- Workload Setup ---
binary_path = options.binary


system.workload = SEWorkload.init_compatible(binary_path) 

process = Process() 
process.cmd = [binary_path] 
system.cpu.workload = process 
system.cpu.createThreads() 

# --- Simulation ---
root = Root(full_system=False, system=system) 
m5.instantiate()

print(f"Beginning simulation for: {binary_path}")
print(f"L1I: size={options.l1i_size} assoc={options.l1i_assoc}")
print(f"L1D: size={options.l1d_size} assoc={options.l1d_assoc}")
if has_l2_cache:
    print(f"L2:  size={options.l2_size} assoc={options.l2_assoc}")
else:
    print("L2:  Disabled")
print(f"Cache block size={options.cache_line_size}")

exit_event = m5.simulate()

print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
