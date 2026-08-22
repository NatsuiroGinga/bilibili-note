// 本文件基于 BlinkDL/RWKV-LM 固定提交的 rwkv7_clampw.cpp 修改。
// 唯一功能修改是将 TORCH_LIBRARY 命名空间改为编译时必填宏。

#include <torch/extension.h>

#ifndef CUDA_RWKV_NAMESPACE
#error "CUDA_RWKV_NAMESPACE must be defined"
#endif

#ifdef _FP32_
using bf = float;
#else
#include <cuda_bf16.h>
using bf = __nv_bfloat16;
#endif

void cuda_forward(int B,
                  int T,
                  int H,
                  bf* r,
                  bf* w,
                  bf* k,
                  bf* v,
                  bf* a,
                  bf* b,
                  bf* y,
                  float* s,
                  float* sa);

void forward(torch::Tensor& r,
             torch::Tensor& w,
             torch::Tensor& k,
             torch::Tensor& v,
             torch::Tensor& a,
             torch::Tensor& b,
             torch::Tensor& y,
             torch::Tensor& s,
             torch::Tensor& sa) {
    int B = r.sizes()[0];
    int T = r.sizes()[1];
    int H = r.sizes()[2];
    cuda_forward(B,
                 T,
                 H,
                 static_cast<bf*>(r.data_ptr()),
                 static_cast<bf*>(w.data_ptr()),
                 static_cast<bf*>(k.data_ptr()),
                 static_cast<bf*>(v.data_ptr()),
                 static_cast<bf*>(a.data_ptr()),
                 static_cast<bf*>(b.data_ptr()),
                 static_cast<bf*>(y.data_ptr()),
                 static_cast<float*>(s.data_ptr()),
                 static_cast<float*>(sa.data_ptr()));
}

void cuda_backward(int B,
                   int T,
                   int H,
                   bf* r,
                   bf* w,
                   bf* k,
                   bf* v,
                   bf* a,
                   bf* b,
                   bf* dy,
                   float* s,
                   float* sa,
                   bf* dr,
                   bf* dw,
                   bf* dk,
                   bf* dv,
                   bf* da,
                   bf* db);

void backward(torch::Tensor& r,
              torch::Tensor& w,
              torch::Tensor& k,
              torch::Tensor& v,
              torch::Tensor& a,
              torch::Tensor& b,
              torch::Tensor& dy,
              torch::Tensor& s,
              torch::Tensor& sa,
              torch::Tensor& dr,
              torch::Tensor& dw,
              torch::Tensor& dk,
              torch::Tensor& dv,
              torch::Tensor& da,
              torch::Tensor& db) {
    int B = r.sizes()[0];
    int T = r.sizes()[1];
    int H = r.sizes()[2];
    cuda_backward(B,
                  T,
                  H,
                  static_cast<bf*>(r.data_ptr()),
                  static_cast<bf*>(w.data_ptr()),
                  static_cast<bf*>(k.data_ptr()),
                  static_cast<bf*>(v.data_ptr()),
                  static_cast<bf*>(a.data_ptr()),
                  static_cast<bf*>(b.data_ptr()),
                  static_cast<bf*>(dy.data_ptr()),
                  static_cast<float*>(s.data_ptr()),
                  static_cast<float*>(sa.data_ptr()),
                  static_cast<bf*>(dr.data_ptr()),
                  static_cast<bf*>(dw.data_ptr()),
                  static_cast<bf*>(dk.data_ptr()),
                  static_cast<bf*>(dv.data_ptr()),
                  static_cast<bf*>(da.data_ptr()),
                  static_cast<bf*>(db.data_ptr()));
}

TORCH_LIBRARY(CUDA_RWKV_NAMESPACE, m) {
    m.def("forward", forward);
    m.def("backward", backward);
}
