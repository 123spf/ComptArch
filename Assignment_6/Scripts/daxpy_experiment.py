
import m5
from m5.objects import *

# used multisim-print-this.py as a guide I was not able to fix it, I did realize the logical next step was to use a board

import gem5.utils.multisim as multisim

from gem5.simulate.simulator import Simulator

# Experiment Parameters

#Thread counts to simulate for the TLP analysis.

thread_counts = [1, 2, 4, 8]

# opLat/issueLat pairs for the FloatSimdFU.
#    Format: (opLat, issueLat)

fu_latency_pairs = [
    (1, 6),
    (2, 5),
    (3, 4),
    (4, 3),
    (5, 2),
    (6, 1),
]

# Path to the compiled multi-threaded daxpy binary.
daxpy_binary = "./multithread_daxpy"


# Custom Functional Unit Pool Definition
# The default values are defined in `MinorDefaultFUPool` inside
# `BaseMinorCPU.py`

class MyFUPool(MinorDefaultFUPool):
    """
    A custom Functional Unit Pool that allows for configurable latencies
    for the Floating-Point/SIMD unit.
    """
    def __init__(self, opLat, issueLat):
        super().__init__()

        # This loop iterates through the list of default functional units
        # provided by MinorDefaultFUPool.

        for i, fu in enumerate(self.funcUnits):

            if isinstance(fu, MinorDefaultFloatSimdFU):
                # Create a new FU instance with desired latencies.
                new_fu = MinorDefaultFloatSimdFU()
                new_fu.opLat = opLat
                new_fu.issueLat = issueLat
                # Replace the default FU with custom one.
                self.funcUnits[i] = new_fu
                
                return

# Custom Cache Hierarchy Definition
#copied from previous assignment, `arm_iotbench.py` script.

class MyL1Cache(Cache):
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20

    def __init__(self, size):
        super(MyL1Cache, self).__init__()
        self.size = size

    def connectBus(self, bus):
        self.mem_side = bus.cpu_side_ports

    def connectCPU(self, cpu_port):
        self.cpu_side = cpu_port

class MyL1ICache(MyL1Cache):
    is_read_only = True
    writeback_clean = True

class MyL1DCache(MyL1Cache):
    pass

class MyL2Cache(Cache):
    tag_latency = 20
    data_latency = 20
    response_latency = 20
    mshrs = 20
    tgts_per_mshr = 12
    write_buffers = 8

    def __init__(self, size):
        super(MyL2Cache, self).__init__()
        self.size = size

    def connectCPUSideBus(self, bus):
        self.cpu_side = bus.mem_side_ports

    def connectMemSideBus(self, bus):
        self.mem_side = bus.cpu_side_ports


#  MultiSim Orchestration

# `set_num_processes` to limit the number of parallel gem5 instances
multisim.set_num_processes(4)

# The `multisim-print-this.py` example uses nested for-loops
# to iterate through different configurations.
# create a simulation run for each combination of thread count and FU latency.

for threads in thread_counts:
    for op_lat, issue_lat in fu_latency_pairs:

        # --- System Configuration (per simulation run) ---
        system = System()
        system.clk_domain = SrcClockDomain(clock="2GHz", voltage_domain=VoltageDomain())
        system.mem_mode = "timing"
        system.mem_ranges = [AddrRange("1GB")]

        system.cpu = [ArmMinorCPU(cpu_id=i) for i in range(threads)]

        my_fu_pool = MyFUPool(opLat=op_lat, issueLat=issue_lat)

        system.l2bus = L2XBar()

        for cpu in system.cpu:
            cpu.executeFuncUnits = my_fu_pool
            
           
            cpu.icache = MyL1ICache(size="32kB")
            cpu.dcache = MyL1DCache(size="64kB")
            
            cpu.icache.connectCPU(cpu.icache_port)
            cpu.dcache.connectCPU(cpu.dcache_port)

            cpu.icache.connectBus(system.l2bus)
            cpu.dcache.connectBus(system.l2bus)

            cpu.createInterruptController()

        system.l2cache = MyL2Cache(size="2MB")
        system.l2cache.connectCPUSideBus(system.l2bus)
        system.membus = SystemXBar()
        system.l2cache.connectMemSideBus(system.membus)

        system.mem_ctrl = MemCtrl()
        system.mem_ctrl.dram = DDR3_1600_8x8()
        system.mem_ctrl.dram.range = system.mem_ranges[0]
        system.mem_ctrl.port = system.membus.mem_side_ports
        system.system_port = system.membus.cpu_side_ports

        # --- Workload Configuration ---
        process = Process(cmd=[daxpy_binary, str(threads)])
        for cpu in system.cpu:
            cpu.workload = process
            cpu.createThreads()

        # --- Simulator Instantiation for MultiSim ---
        sim_id = f"daxpy_{threads}t_op{op_lat}_issue{issue_lat}"
        simulator = Simulator(
            board=system,
            id=sim_id,
        )
        multisim.add_simulator(simulator)
