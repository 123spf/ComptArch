#cc = gcc
#prom = main
#deph = benchmark.h
#obj = main.o list_search_sort.o matrix.o conv.o
#source = main.c list_search_sort.c matrix.c conv.c

CC = gcc -static
ACC = aarch64-linux-gnu-gcc -static
RCC = riscv64-linux-gnu-gcc -static
OUTFLAG = -o


CORE_FILES  = list_search_sort conv main matrix 
ORIG_SRCS = $(addsuffix .c, $(CORE_FILES))
OBJS = $(addsuffix .o,$(CORE_FILES))
#OUTFILE_X86 = iotbench-x86-$(SID)
#OUTFILE_RISCV =  iotbench-RISCV-$(SID)
#OUTFILE_ARM = iotbench-ARM-$(SID)

HEADERS = benchmark.h



# Configuration 1: Basic Wearable Profiling
BENCH_FLAGS_CONFIG1 = -DTOTAL_DATA_SIZE=6144 \
                      -DTEST_TYPE=0 \
                      -DDATA_DIM=1 \
                      -DCALCULATE_ACCURACY=1 \
                      -DNUM_ITERATE=10              
					 
                    

OUTFILE_ARM_CONFIG1 = iotbench-ARM-basic

# Configuration 2: Advanced Wearable Profiling
BENCH_FLAGS_CONFIG2 = -DTOTAL_DATA_SIZE=12288 \
                      -DTEST_TYPE=1 \
                      -DDATA_DIM=1 \
                      -DCALCULATE_ACCURACY=2 \
                      -DNUM_ITERATE=20

OUTFILE_ARM_CONFIG2 = iotbench-ARM-advanced




.PHONY: riscv 
riscv: 
	$(RCC) $(OUTFLAG) $(OUTFILE_RISCV) $(ORIG_SRCS)
#%.o:%.c $(HEADERS)
#	$(RCC) -c $< $(OUTFLAG) $@


.PHONY: arm 
arm: 
	$(ACC) $(OUTFLAG) $(OUTFILE_ARM) $(ORIG_SRCS)
#%.o:%.c $(HEADERS)
#	$(ACC) -c $< $(OUTFLAG) $@


.PHONY: arm_basic
arm_basic:
	$(ACC) $(BENCH_FLAGS_CONFIG1) $(OUTFLAG) $(OUTFILE_ARM_CONFIG1) $(ORIG_SRCS)


.PHONY: arm_advanced
arm_advanced:
	$(ACC) $(BENCH_FLAGS_CONFIG2) $(OUTFLAG) $(OUTFILE_ARM_CONFIG2) $(ORIG_SRCS)



.PHONY: x86 
x86: 
	$(CC) $(OUTFLAG) $(OUTFILE_X86) $(ORIG_SRCS)

#$(prom):$(obj)
#	$(cc) -o $(prom) $(obj)

#%.o:%.c $(deps)
#	gcc -c $< -o $@

#.PHONY: clean
#clean:
#	rm -f $(OUTFILE_ARM) $(OUTFILE_RISCV) $(OUTFILE_X86)
#clean:
#	rm -rf $(obj) $(prom)

.PHONY: clean
clean:
	rm -f $(OUTFILE_ARM_CONFIG1) $(OUTFILE_ARM_CONFIG2) iotbench-ARM-$(SID)-default iotbench-RISCV-$(SID) iotbench-x86-$(SID)
