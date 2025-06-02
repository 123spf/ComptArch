import m5
from m5.objects import *
from caches import L1ICache, L1DCache, L2Cache


import os

system = System()

# CPU
system.cpu = ArmO3CPU()
system.membus = SystemXBar()

system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MiB")]

# Create L1 Caches
system.cpu.icache = L1ICache() 
system.cpu.dcache = L1DCache() 

# Create a memory bus for the L2 cache (L2 Bus)
system.l2bus = SystemXBar()

# Create L2 Cache
system.l2cache = L2Cache() 


# Connect L1 Caches to the CPU
system.cpu.icache.connectCPU(system.cpu) 
system.cpu.dcache.connectCPU(system.cpu) 

# Connect the L1 Caches to the L2 Bus
system.cpu.icache.connectBus(system.l2bus) #
system.cpu.dcache.connectBus(system.l2bus) #

# Connect the L2 Cache to the L2 Bus (CPU side) and the main memory bus (memory side)
system.l2cache.connectCPUSideBus(system.l2bus) #
system.l2cache.connectMemSideBus(system.membus)

system.cpu.createInterruptController()

system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports

thispath = os.path.dirname(os.path.realpath(__file__))
binary = os.path.join(
    thispath,
    "../../../",
    "configs/learning_gem5/IoTBench/iotbench-ARM-advanced",
)

system.workload = SEWorkload.init_compatible(binary)

process = Process()
process.cmd = [binary]
system.cpu.workload = process
system.cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

print(f"Beginning simulation!")
exit_event = m5.simulate()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
