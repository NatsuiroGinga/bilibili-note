---
title: "RFC 9287：QUIC 固定位随机化与识别边界"
authors: [Martin Thomson]
year: 2022
date: 2026-07-30
journal: "RFC Editor，RFC 9287"
source_pdf: "[[raw/papers/pinn/protocol-adaptive/2022-RFC9287-QUIC-Bit-Greasing.pdf]]"
zotero_item_key: "8EJXXNCA"
zotero_citekey: "thomson_greasing_2022"
zotero_attachment_key: "XREFGV99"
sha256: "b2f3f53901dcb88bd5cff2f3fe31a5fc6c0c4c04e0492ad34171db48eb1af688"
key_finding: "端点协商 grease_quic_bit 后应把 QUIC 固定位设为不可预测值，因此固定值只能是识别证据之一，不能成为硬判据。"
tags:
  - QUIC
  - 协议规范
  - 协议识别
  - 类型/论文
aliases:
  - RFC9287
  - QUIC Bit Greasing
---

# RFC 9287：QUIC 固定位随机化与识别边界

## 一句话

把首字节第二高位恒为 1 当作 QUIC 硬签名已经不符合现行标准轨迹。

## 原文证据

- PDF 第 2 页、第 1 节：固定值原本便于区分 QUIC，但依赖该值会造成协议僵化。
- PDF 第 3 至 4 页、第 3.1 节：双方协商 `grease_quic_bit` 后，端点应把该位设为不可预测值，并可在满足规范条件时设为 0。
- PDF 第 4 页、第 3.2 节：任何赋予该位新语义的扩展必须先协商，观察者不能直接解释随机值。
- PDF 第 4 页、安全考虑：该扩展会让没有端点协作的 QUIC 识别更困难。

## 对 R2 的约束

- 协议识别器必须组合长首部版本、连接行为、包形态和握手证据，并输出校准概率；固定值只作候选字段。
- 固定位为 0 的样本不得直接回退为普通 UDP；低置信样本走未知分支。
- 留一版本与无握手负对照必须包含可能使用固定位随机化的样本。

## 文献信息

- DOI：10.17487/RFC9287
- 官方页面：https://www.rfc-editor.org/info/rfc9287
