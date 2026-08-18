"""Dijk 2026（SSRN 6597680）附录 A 的 83 个输入字段与协议常量。

字段顺序严格照抄论文附录 A（印刷第 48 页）的列举顺序，不做任何重排或增删。
本模块只含常量，不含任何可执行逻辑。
"""

from __future__ import annotations

from typing import Final

# 论文附录 A 逐条列举的 83 个字段，顺序即张量列顺序。
DIJK_FEATURES: Final[tuple[str, ...]] = (
    # • SrcPort, DstPort, Protocol, Flow Duration, Flow Bytes/s, Flow Packets/s
    "SrcPort",
    "DstPort",
    "Protocol",
    "Flow Duration",
    "Flow Bytes/s",
    "Flow Packets/s",
    # • Tot Fwd Pkts, Tot Bwd Pkts, Total Length of Fwd Packet, Total Length of Bwd Packet
    "Tot Fwd Pkts",
    "Tot Bwd Pkts",
    "Total Length of Fwd Packet",
    "Total Length of Bwd Packet",
    # • Fwd Packet Length Min/Max/Mean/Std, Bwd Packet Length Min/Max/Mean/Std
    "Fwd Packet Length Min",
    "Fwd Packet Length Max",
    "Fwd Packet Length Mean",
    "Fwd Packet Length Std",
    "Bwd Packet Length Min",
    "Bwd Packet Length Max",
    "Bwd Packet Length Mean",
    "Bwd Packet Length Std",
    # • Flow IAT Mean/Min/Max/Stddev
    "Flow IAT Mean",
    "Flow IAT Min",
    "Flow IAT Max",
    "Flow IAT Stddev",
    # • Fwd IAT Min/Max/Mean/Std/Tot
    "Fwd IAT Min",
    "Fwd IAT Max",
    "Fwd IAT Mean",
    "Fwd IAT Std",
    "Fwd IAT Tot",
    # • Bwd IAT Min/Max/Mean/Std/Tot
    "Bwd IAT Min",
    "Bwd IAT Max",
    "Bwd IAT Mean",
    "Bwd IAT Std",
    "Bwd IAT Tot",
    # • Fwd PSH flags, Bwd PSH flags, Fwd URG flags, Bwd URG flags
    "Fwd PSH flags",
    "Bwd PSH flags",
    "Fwd URG flags",
    "Bwd URG flags",
    # • Fwd Header Length, Bwd Header Length
    "Fwd Header Length",
    "Bwd Header Length",
    # • Fwd Packets/s, Bwd Packets/s
    "Fwd Packets/s",
    "Bwd Packets/s",
    # • Packet Length Min/Max/Mean/Std/Variance
    "Packet Length Min",
    "Packet Length Max",
    "Packet Length Mean",
    "Packet Length Std",
    "Packet Length Variance",
    # • FIN/SYN/RST/PSH/ACK/URG/CWR/ECE Flag Cnt
    "FIN Flag Cnt",
    "SYN Flag Cnt",
    "RST Flag Cnt",
    "PSH Flag Cnt",
    "ACK Flag Cnt",
    "URG Flag Cnt",
    "CWR Flag Cnt",
    "ECE Flag Cnt",
    # • Down/Up Ratio, Average Packet Size, Fwd Segment Size Avg, Bwd Segment Size Avg
    "Down/Up Ratio",
    "Average Packet Size",
    "Fwd Segment Size Avg",
    "Bwd Segment Size Avg",
    # • Fwd/Bwd Bytes|Packet|Bulk Rate Avg
    "Fwd Bytes/Bulk Avg",
    "Fwd Packet/Bulk Avg",
    "Fwd Bulk Rate Avg",
    "Bwd Bytes/Bulk Avg",
    "Bwd Packet/Bulk Avg",
    "Bwd Bulk Rate Avg",
    # • Subflow Fwd Packets, Subflow Fwd Bytes, Subflow Bwd Packets, Subflow Bwd Bytes
    "Subflow Fwd Packets",
    "Subflow Fwd Bytes",
    "Subflow Bwd Packets",
    "Subflow Bwd Bytes",
    # • FWD Init Win Bytes, Bwd Init Win Bytes, Fwd Act Data Pkts, Fwd Seg Size Min
    "FWD Init Win Bytes",
    "Bwd Init Win Bytes",
    "Fwd Act Data Pkts",
    "Fwd Seg Size Min",
    # • Active Min/Mean/Max/Std, Idle Min/Mean/Max/Std
    "Active Min",
    "Active Mean",
    "Active Max",
    "Active Std",
    "Idle Min",
    "Idle Mean",
    "Idle Max",
    "Idle Std",
    # • L3/L4 Protocol, Int/Ext Dst IP
    "L3/L4 Protocol",
    "Int/Ext Dst IP",
    # • External_src, External_dst
    "External_src",
    "External_dst",
)

# 时间与标签列（不进入特征矩阵）。
TIME_START_COLUMN: Final[str] = "mTimestampStart"
TIME_LAST_COLUMN: Final[str] = "mTimestampLast"
LABEL_COLUMN: Final[str] = "Label"

# 本课题 77 维防泄漏臂没有、而 Dijk 83 维含有的 6 个身份/位置字段。
DIJK_ONLY_FIELDS: Final[tuple[str, ...]] = (
    "SrcPort",
    "DstPort",
    "L3/L4 Protocol",
    "Int/Ext Dst IP",
    "External_src",
    "External_dst",
)

# 论文表 2 与 §5.6 明写的协议常量。
SEQUENCE_LENGTH: Final[int] = 128          # 表 2：Maximum sequence length (L) = 128 flows
SESSION_GAP_SECONDS: Final[int] = 300      # 表 2：inactivity threshold ∆ = 300 s（OP 不用）
RANDOM_SEED: Final[int] = 42               # §5.8：fixed random seed (42)

XGBOOST_PARAMS: Final[dict[str, object]] = {
    "learning_rate": 0.05,
    "max_depth": 8,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_lambda": 1.0,
    "min_child_weight": 1.0,
    "max_bin": 256,
    "tree_method": "hist",
    "objective": "binary:logistic",
}
XGBOOST_NUM_BOOST_ROUND: Final[int] = 800  # §5.6：number of estimators = 800

# LSPR24 最终封存区边界（来自冻结数据合同 splits.target_final_cut_ns）。
# 本运行对 available_ns >= 该值的行在读取标签与特征前丢弃，且不计数、不哈希。
TARGET_FINAL_CUT_NS: Final[int] = 1709802623000000000

assert len(DIJK_FEATURES) == 83, f"字段数必须为 83，实为 {len(DIJK_FEATURES)}"
assert len(set(DIJK_FEATURES)) == 83, "字段清单存在重复"
