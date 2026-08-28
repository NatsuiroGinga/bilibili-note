#include <cuda_runtime.h>

#include <cstdio>

#define CUDA_CHECK(call)                                                        \
    do {                                                                        \
        const cudaError_t error = (call);                                       \
        if (error != cudaSuccess) {                                             \
            std::fprintf(stderr, "CUDA 错误: %s (%s:%d)\n",                    \
                         cudaGetErrorString(error), __FILE__, __LINE__);         \
            return 1;                                                           \
        }                                                                       \
    } while (0)

__global__ void add_one(int* value) {
    if (threadIdx.x == 0 && blockIdx.x == 0) {
        *value += 1;
    }
}

int main() {
    cudaDeviceProp properties{};
    CUDA_CHECK(cudaGetDeviceProperties(&properties, 0));

    int host_value = 41;
    int result = 0;
    int* device_value = nullptr;
    CUDA_CHECK(cudaMalloc(&device_value, sizeof(int)));
    CUDA_CHECK(cudaMemcpy(device_value, &host_value, sizeof(int), cudaMemcpyHostToDevice));

    add_one<<<1, 1>>>(device_value);
    CUDA_CHECK(cudaGetLastError());
    CUDA_CHECK(cudaDeviceSynchronize());
    CUDA_CHECK(cudaMemcpy(&result, device_value, sizeof(int), cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaFree(device_value));

    if (result != 42 || properties.major != 12 || properties.minor != 0) {
        std::fprintf(stderr,
                     "验证值不符: result=%d capability=%d.%d\n",
                     result,
                     properties.major,
                     properties.minor);
        return 2;
    }

    std::printf(
        "{\"status\":\"ok\",\"result\":%d,\"device\":\"%s\",\"capability\":\"%d.%d\"}\n",
        result,
        properties.name,
        properties.major,
        properties.minor);
    return 0;
}
