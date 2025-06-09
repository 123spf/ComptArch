// daxpy.cpp (snippet with correct header)
#include <cstdio>
#include <random>
#include "gem5/m5ops.h" // Corrected header name

    // ... (initialization code from homework PDF) ...

  int main()
  {
    const int N = 1000;
    double X[N], Y[N], alpha = 0.5;
    std::random_device rd; std::mt19937 gen(rd());
    std::uniform_real_distribution<> dis(1, 2);
    for (int i = 0; i < N; ++i)
    {
      X[i] = dis(gen);
      Y[i] = dis(gen);
    }

    // Start of daxpy loop
    m5_dump_reset_stats(0,0); // Add this
    for (int i=0; i<N; ++i) 
    {
        Y[i] = alpha*X[i] + Y[i];
    }


    // End of daxpy loop
    m5_dump_reset_stats(0,0); 
    double sum = 0;
    for (int i = 0; i < N; ++i)
    {
      sum += Y[i];
    }
    printf("%lf\n", sum);
    return 0;
}
