CC = aarch64-linux-gnu-gcc
CFLAGS = -march=armv8-a+nosimd -O2 -fno-tree-vectorize -static
LDFLAGS = -static # Though --static in CFLAGS often handles this for gcc

SRCS = FloatMM.c
PROG = FloatMM_scalar

all: $(PROG)

$(PROG): $(SRCS)
	$(CC) $(CFLAGS) $^ -o $@ $(LDFLAGS) -lm

clean:
	rm -f $(PROG)
