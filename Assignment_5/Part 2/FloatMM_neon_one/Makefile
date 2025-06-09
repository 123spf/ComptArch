CC = aarch64-linux-gnu-gcc
# Flags to encourage NEON vectorization:
# -O3 is a high optimization level that typically enables auto-vectorization.
# -march=armv8-a (or armv8-a+simd) ensures the target supports NEON.
# -ffast-math can sometimes help vectorization by allowing reordering of FP ops.
# -ftree-vectorize (explicitly enable, though often on by default with -O3)
CFLAGS = -march=armv8-a -O3 -ftree-vectorize -ffast-math -static
LDFLAGS = -static

SRCS = FloatMM.c
PROG = FloatMM_neon

all: $(PROG)

$(PROG): $(SRCS)
	$(CC) $(CFLAGS) $^ -o $@ $(LDFLAGS) -lm

clean:
	rm -f $(PROG)
