// multithread_daxpy.cpp
// Multi-threaded DAXPY implementation using pthreads for gem5 simulation.

#include <pthread.h>
#include <iostream>
#include <vector>
#include <cstdlib>

// gem5 m5ops include
#if defined(__aarch64__)
#include "gem5/m5ops.h"
#endif

// Struct to pass arguments to each thread
struct ThreadData {
    int thread_id;
    int num_threads;
    long long n;
    double alpha;
    double* x;
    double* y;
};

// The function each thread will execute
void* daxpy_thread_func(void* arg) {
    ThreadData* data = (ThreadData*)arg;

    // Calculate the chunk of the vector this thread will process
    long long chunk_size = data->n / data->num_threads;
    long long start = data->thread_id * chunk_size;
    long long end = (data->thread_id == data->num_threads - 1) ? data->n : start + chunk_size;

    for (long long i = start; i < end; ++i) {
        data->y[i] = data->alpha * data->x[i] + data->y[i];
    }

    pthread_exit(NULL);
    return NULL; // Return NULL to avoid compiler warnings
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <num_threads>" << std::endl;
        return 1;
    }

    int num_threads = atoi(argv[1]);
    if (num_threads <= 0) {
        std::cerr << "Number of threads must be a positive integer." << std::endl;
        return 1;
    }

    long long n = 10000; // Size of the vectors
    double alpha = 2.0;   // Scalar alpha value

    // Allocate and initialize vectors
    std::vector<double> x_vec(n, 1.0);
    std::vector<double> y_vec(n, 2.0);
    double* x = x_vec.data();
    double* y = y_vec.data();

    // Create thread handles and data structs
    pthread_t threads[num_threads];
    ThreadData thread_data[num_threads];

    std::cout << "Starting multi-threaded DAXPY with " << num_threads << " threads." << std::endl;

    // --- Region of Interest (ROI) Starts Here ---
#if defined(__aarch64__)
    m5_dump_reset_stats(0, 0);
#endif

    // Create and launch threads
    for (int i = 0; i < num_threads; ++i) {
        thread_data[i] = {i, num_threads, n, alpha, x, y};
        int rc = pthread_create(&threads[i], NULL, daxpy_thread_func, (void*)&thread_data[i]);
        if (rc) {
            std::cerr << "Error:unable to create thread," << rc << std::endl;
            exit(-1);
        }
    }

    // Wait for all threads to complete
    for (int i = 0; i < num_threads; ++i) {
        pthread_join(threads[i], NULL);
    }

    // --- Region of Interest (ROI) Ends Here ---
#if defined(__aarch64__)
    m5_dump_reset_stats(0, 0);
#endif

    std::cout << "DAXPY calculation finished." << std::endl;

    // Optional: verification check for one element
    // std::cout << "Verification: y[0] = " << y[0] << std::endl;

    return 0;
}
