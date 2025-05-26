# Import necessary gem5 components
from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_shared_l2_cache_hierarchy import PrivateL1SharedL2CacheHierarchy
from gem5.components.memory.single_channel import SingleChannelDDR4_2400 

from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.resources.resource import obtain_resource # To get a pre-built workload
from gem5.simulate.simulator import Simulator




# Set up the cache hierarchy.
# Using PrivateL1SharedL2CacheHierarchy for a common setup.

cache_hierarchy = PrivateL1SharedL2CacheHierarchy(
    l1d_size="32KiB",  # L1 Data Cache Size
    l1i_size="32KiB",  # L1 Instruction Cache Size
    l2_size="256KiB",   # L2 Cache Size
)

# Set up the system memory.
memory = SingleChannelDDR4_2400(size="2GB")

# Set up the processor.
processor = SimpleProcessor(
    cpu_type=CPUTypes.TIMING, 
    num_cores=1,
    isa=ISA.X86
)


# Set up the board and connect components.

board = SimpleBoard(
    clk_freq="3GHz", 
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

board.cache_line_size = 32

# Set the workload for the processor.
# pre-built x86 benchmark.
binary = obtain_resource("x86-npb-lu-size-s")
board.set_se_binary_workload(binary)



# Set up the simulator and run the simulation.
simulator = Simulator(board=board)
print("Beginning simulation!")
simulator.run()
print("Simulation_finished!")
