import m5
from m5.objects import *
import os
from caches import *


system = System()

system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MiB")]



# Create L1 Caches
system.cpu = ArmMinorCPU() 
                           

system.l1i_cache = L1ICache()
system.l1d_cache = L1DCache()


system.l1i_cache = L1ICache()
system.l1d_cache = L1DCache()



# Create the CPU
system.cpu = ArmMinorCPU()
#system.cpu.branchPred = NULL  # Disable branch prediction


system.membus = SystemXBar()



# Connect CPU to L1 Caches
system.cpu.icache_port = system.l1i_cache.cpu_side
system.cpu.dcache_port = system.l1d_cache.cpu_side

# Connect L1 Caches to the memory bus
system.l1i_cache.mem_side = system.membus.cpu_side_ports
system.l1d_cache.mem_side = system.membus.cpu_side_ports



system.cpu.createInterruptController() 


system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports # membus.mem_side_ports connects to memory

system.system_port = system.membus.cpu_side_ports # For functional access


thispath = os.path.dirname(os.path.realpath(__file__))
binary = os.path.join(
    thispath,
    "../../../",
    "tests/test-progs/hello/bin/arm/linux/hello",
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
