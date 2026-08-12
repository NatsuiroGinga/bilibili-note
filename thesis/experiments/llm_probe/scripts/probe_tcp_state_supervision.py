"""D1/D2/V1/V2/V3：TCP 发送者状态监督目标的最小证伪探针（只读分析，非训练实验）。

裁决对象是候选修正案 A'——用 TCP 发送者动力学状态（RTT、cwnd、在途字节等）
替代已退化的「队列守恒残差」作为 E2 共享 PINN 的物理监督。本脚本回答一个
问题：这些状态量作为监督目标是否具备非退化性、对照分辨力和可学性。

- D1（非退化与置换分辨力）：在 ``train-fit`` 且 ``transport_family == "TCP"``
  的窗口子集上，对每个状态通道检查有效值比例、分层内标准差中位数、分层内
  置换后的平均绝对变化，以及动力学残差真值侧是否有内容（cwnd 变化或丢包）。
- D2（可预测性探针）：按 ``physics_group_sha256`` 分组五折交叉验证，用七个
  常规字段（duration/orig_bytes/...）预测每个状态通道，报告岭回归与两层
  MLP 的折外（out-of-fold）R²，并按预注册判据裁决 A' 是否可以进入合同修订。

D1/D2 证伪 A'（TCP 状态监督）之后，V1/V2/V3 进一步裁决一个更结构性的命题：
E2 物理池的信息是否几乎全部装在场景配置（``evaluation_cluster_id``）里而非
窗口动态里——若成立，物理辅助监督路线正式关闭；若窗口内动态量仍有场景解释
不到的方差，则残差型监督仍可能保留窄门。

- V1（场景中心化可预测性）：目标与七字段特征都先减去所属场景
  （``evaluation_cluster_id``）的组内均值，再看分组交叉验证折外 R²（记为
  R²_within）是否退化；另设对照——只用「所属场景七字段组内均值」这一场景
  指纹去预测原始未中心化目标，得 R²_between，检验知道场景身份本身就能解释
  多少方差。
- V2（场景可分性探针）：直接用七字段（或状态目标）分类 128 个场景，看
  top-1 准确率是否远超机会水平，检验七字段或状态量本身是否就是场景身份的
  确定性函数。
- V3（动态量方差分解）：对 cwnd 窗口净变化、丢包事件计数、cwnd 收缩事件
  计数重复场景间/场景内方差分解，检验窗口内「动态」是否与状态「水平」一样
  被场景钉死。

判据阈值、随机种子、交叉验证折数、模型超参数网格均在任务派发阶段冻结为
本模块的模块级常量（见下方常量区），不提供命令行覆盖入口，防止看到真实
探针结果后再调参。数据路径与输出路径可通过命令行指定。

跨发送者聚合口径：tcp-sender-truth-v2 制品逐窗口有 8 个发送者，而七字段
预测特征逐窗口只有 1 行，必须先把发送者级真值折叠到窗口级才能与七字段
对齐。RTT 类量使用按 ``truth_tcp_rtt_sample_count`` 加权的均值（只对
``*_observed`` 为真的发送者聚合，语义与
``src/flow_probe/r2_final_physics_fit.py`` 中 ``_aggregate_tcp_sender_truth``
对 RTT 的处理一致）；cwnd、在途字节这类「总量型」状态同时给出求和与均值
两种聚合，不静默只选一种——求和对应窗口级网络总占用（与既有生产聚合函数
对 cwnd/bytes_in_flight 采用的求和口径一致，是 A' 若复用该聚合函数时的
实际监督目标形态），均值对应典型单发送者状态。ssthresh 存在 Linux
TCP_INFINITE_SSTHRESH 哨兵值 ``2**32 - 1``（与
``configs/r2_final_physics_fit_seed42_tcp_udp_v3_formal.yaml`` 的
``data.tcp_supervision.ssthresh_unset_value`` 一致），聚合前先剔除哨兵值，
否则会被当作 42 亿量级的巨大观测值污染求和与均值。
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class TcpStateProbeError(RuntimeError):
    """D1/D2/V1/V2/V3 探针在数据契约被破坏或前置条件不满足时抛出。"""


# ---------------------------------------------------------------------------
# 预注册冻结常量。
#
# 全部判据阈值、随机种子、交叉验证折数与模型超参数在任务派发阶段随裁决
# 方法一起冻结，不得在看到真实探针数值后修改，也不提供命令行覆盖入口，
# 作为防止事后调参的机制保障。
# ---------------------------------------------------------------------------

#: 全局随机种子，覆盖分层置换模拟与模型初始化。
RANDOM_SEED: int = 42

#: D2 外层分组交叉验证折数，分组键为 physics_group_sha256，防止同一物理组跨折泄漏。
N_GROUP_FOLDS: int = 5

#: 岭回归内层折内 alpha 选择所用的分组交叉验证折数上限。
RIDGE_INNER_FOLDS: int = 3

#: 岭回归 alpha 网格；输入与目标均先标准化，网格跨通道通用。
RIDGE_ALPHA_GRID: tuple[float, ...] = (0.01, 0.1, 1.0, 10.0, 100.0, 1000.0)

#: 两层 MLP 隐藏层结构：两个隐藏层，每层 64 个单元。
MLP_HIDDEN_LAYER_SIZES: tuple[int, ...] = (64, 64)
MLP_MAX_ITER: int = 500
MLP_VALIDATION_FRACTION: float = 0.1
MLP_N_ITER_NO_CHANGE: int = 15

#: D1 项 1：各通道有效值（观测掩码为真且非哨兵）比例下限。
MIN_OBSERVED_VALID_RATIO: float = 0.90

#: D1 项 2：按 evaluation_cluster_id 分层，层内 z 标准化目标标准差中位数下限。
MIN_STRATUM_TARGET_STD_MEDIAN_Z: float = 0.2

#: D1 项 3：分层内一次无固定点置换后，目标逐元素平均绝对变化（z 单位）下限。
MIN_PERMUTATION_MEAN_ABS_DELTA_Z: float = 0.1

#: D1 项 4：cwnd 窗口净变化非零或丢包事件计数 > 0 的窗口比例下限。
MIN_DYNAMICS_EVIDENCE_WINDOW_RATIO: float = 0.30

#: D2 预注册判据：全部通道全部模型 R² 低于该值 → A' 否决。
D2_DEGENERATE_R2_THRESHOLD: float = 0.1

#: D2 预注册判据：最优通道 R² 超过该值 → 警示状态可能是七字段的确定函数。
D2_NEAR_DETERMINISTIC_R2_THRESHOLD: float = 0.9

#: D2 既有结果：最优通道（bytes_in_flight_end_bytes_mean，MLP）折外分组 CV R²。
#: V1 的 R²_between 强形式阈值以此为参照基准（见下方 V1_BETWEEN_R2_STRONG_FORM_THRESHOLD）。
D2_BEST_CHANNEL_REFERENCE_R2: float = 0.8412

#: TCP ssthresh 未设置哨兵值（Linux TCP_INFINITE_SSTHRESH，2**32 - 1）。
TCP_SSTHRESH_UNSET_VALUE: float = 4294967295.0

#: e2 物理辅助制品中的七个字段预测特征（D2 输入）。
FEATURE_COLUMNS: tuple[str, ...] = (
    "duration",
    "orig_bytes",
    "resp_bytes",
    "orig_pkts",
    "resp_pkts",
    "orig_ip_bytes",
    "resp_ip_bytes",
)

#: 窗口级连接键，两份制品共有。
JOIN_KEYS: tuple[str, ...] = ("sequence_id", "window_index_in_sequence")

#: 只读分析限定的划分。
TRAIN_FIT_SPLIT_ID: str = "train-fit"

#: 只读分析限定的传输族。
TCP_TRANSPORT_FAMILY: str = "TCP"

DEFAULT_E2_PATH: Path = Path(
    "runs/data-prepared/e2-physics-auxiliary-v1/e2-physics-auxiliary-v1.parquet"
)
DEFAULT_TCP_PATH: Path = Path(
    "runs/data-prepared/r2-final-tcp-udp-physics-v3/tcp-sender-truth-v2.parquet"
)

# ---------------------------------------------------------------------------
# V1（场景中心化可预测性）预注册冻结常量。
# ---------------------------------------------------------------------------

#: V1 强形式判据分量 1：R²_within（组内中心化后的折外 R²，取岭回归与 MLP 中
#: 较大者）须低于该值，逐通道判定。
V1_WITHIN_R2_STRONG_FORM_THRESHOLD: float = 0.1

#: V1 否决判据：任一通道 R²_within 达到该值即整体否决强形式，窄门保留。
V1_WITHIN_R2_REJECT_THRESHOLD: float = 0.3

#: V1 强形式判据分量 2 的基准比例：R²_between 须达到 D2 已知最优通道折外
#: R² 的这一比例。
V1_BETWEEN_R2_STRONG_FORM_FRACTION: float = 0.7

#: V1 强形式判据分量 2：R²_between（取岭回归与 MLP 中较大者）须达到该阈值，
#: 逐通道判定。0.7 * 0.8412 = 0.58884（在模块加载时由上两个常量算出，不是
#: 手写字面量，避免与基准值脱节）。
V1_BETWEEN_R2_STRONG_FORM_THRESHOLD: float = (
    V1_BETWEEN_R2_STRONG_FORM_FRACTION * D2_BEST_CHANNEL_REFERENCE_R2
)

# ---------------------------------------------------------------------------
# V2（场景可分性探针）预注册冻结常量。
# ---------------------------------------------------------------------------

#: V2 判据：七字段直接分类 128 个 evaluation_cluster_id 的 top-1 准确率
#: （取逻辑回归与随机森林中较大者）达到该阈值 → 七字段本身强编码场景身份。
V2_FIELD_TOP1_ACCURACY_THRESHOLD: float = 0.5

#: V2 附加判据（非预注册强形式判据，用于报出「状态 ≈ 场景 ID 的函数」这一
#: 定性描述的量化口径）：状态目标分类 top-1 准确率达到该值视为「接近全对」。
V2_STATE_NEAR_PERFECT_TOP1_ACCURACY_THRESHOLD: float = 0.9

#: 128 个 evaluation_cluster_id 均匀随机猜测的机会水平，仅用于报告对照。
V2_CHANCE_LEVEL_TOP1_ACCURACY: float = 1.0 / 128.0

#: V2 按窗口序号（非随机）切分训练/测试：每个场景取前该比例的
#: source_window_index 作训练，其余作测试，避免同场景相邻窗口跨集合泄漏。
V2_TRAIN_WINDOW_FRACTION: float = 0.8

#: V2 随机森林分类器树数量。
V2_RANDOM_FOREST_N_ESTIMATORS: int = 300

#: V2 逻辑回归分类器最大迭代步数（128 类多项逻辑回归需要较多步数收敛）。
V2_LOGISTIC_REGRESSION_MAX_ITER: int = 2000

# ---------------------------------------------------------------------------
# V3（动态量方差分解）预注册冻结常量。
# ---------------------------------------------------------------------------

#: V3 判据：场景间/场景内方差比低于该值 → 动态量未被场景主导，残差型监督
#: 仍有真值侧内容。
V3_DYNAMICS_NOT_DOMINATED_RATIO_THRESHOLD: float = 10.0

#: V3 判据：场景间/场景内方差比达到该值 → 强形式对动态量同样成立。
V3_DYNAMICS_STRONG_FORM_RATIO_THRESHOLD: float = 70.0


# ---------------------------------------------------------------------------
# 状态通道聚合规格。
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChannelSpec:
    """单个 TCP 状态通道的跨发送者聚合规格。"""

    #: 通道基名，用于派生输出列名。
    name: str
    #: 发送者级真值列。
    value_col: str
    #: 发送者级观测掩码列。
    mask_col: str
    #: 聚合方式：``weighted_mean`` 按权重列加权平均；``sum_and_mean``
    #: 同时输出 ``{name}_sum`` 与 ``{name}_mean`` 两列。
    kind: Literal["weighted_mean", "sum_and_mean"]
    #: ``weighted_mean`` 必需的权重列（如 RTT 样本数）。
    weight_col: str | None = None
    #: 需要在聚合前剔除的哨兵值（如 ssthresh 的未设置标记）。
    unset_sentinel: float | None = None


#: TCP 状态监督候选通道。RTT 只给均值（求和无物理意义）；cwnd、在途字节、
#: ssthresh 属于「总量型」状态，同时给出求和与均值两种聚合，避免事后只选
#: 一种造成的隐藏设计选择。
TCP_STATE_CHANNEL_SPECS: tuple[ChannelSpec, ...] = (
    ChannelSpec(
        name="rtt_mean_ms",
        value_col="truth_tcp_rtt_mean_ms",
        mask_col="rtt_observed",
        kind="weighted_mean",
        weight_col="truth_tcp_rtt_sample_count",
    ),
    ChannelSpec(
        name="cwnd_end_bytes",
        value_col="truth_tcp_cwnd_end_bytes",
        mask_col="cwnd_end_observed",
        kind="sum_and_mean",
    ),
    ChannelSpec(
        name="bytes_in_flight_end_bytes",
        value_col="truth_tcp_bytes_in_flight_end_bytes",
        mask_col="bytes_in_flight_end_observed",
        kind="sum_and_mean",
    ),
    ChannelSpec(
        name="ssthresh_end_bytes",
        value_col="truth_tcp_ssthresh_end_bytes",
        mask_col="ssthresh_end_observed",
        kind="sum_and_mean",
        unset_sentinel=TCP_SSTHRESH_UNSET_VALUE,
    ),
)

#: 窗口分组键列，聚合后随窗口一起保留。
_GROUP_KEY_COLUMNS: tuple[str, ...] = (
    "physics_group_sha256",
    "evaluation_cluster_id",
    "transport_family",
    "split_id",
)

#: V2/V3 按窗口序号切分所需的场景内窗口序号列，来自 e2 制品，随窗口一起保留。
_WINDOW_ORDER_COLUMN: str = "source_window_index"


def state_channel_output_columns() -> tuple[str, ...]:
    """按 TCP_STATE_CHANNEL_SPECS 派生 D1/D2 实际使用的通道输出列名。"""
    columns: list[str] = []
    for spec in TCP_STATE_CHANNEL_SPECS:
        if spec.kind == "weighted_mean":
            columns.append(spec.name)
        else:
            columns.append(f"{spec.name}_sum")
            columns.append(f"{spec.name}_mean")
    return tuple(columns)


def _channel_valid_column(output_col: str) -> str:
    """把通道输出列名映射到其有效性掩码列名（sum/mean 共用同一掩码）。"""
    for suffix in ("_sum", "_mean"):
        if output_col.endswith(suffix):
            return f"{output_col[: -len(suffix)]}_valid"
    return f"{output_col}_valid"


# ---------------------------------------------------------------------------
# 数据装载与跨发送者聚合。
# ---------------------------------------------------------------------------


def aggregate_tcp_state_channels(tcp_frame: pd.DataFrame) -> pd.DataFrame:
    """把逐发送者 TCP 真值表折叠为逐窗口状态通道表。

    Args:
        tcp_frame: tcp-sender-truth-v2 制品的行（每窗口 8 个发送者一行）。

    Returns:
        DataFrame，每行对应 JOIN_KEYS 唯一确定的一个窗口，含窗口分组键
        （physics_group_sha256、evaluation_cluster_id、transport_family、
        split_id）与 state_channel_output_columns() 列出的每个通道聚合值，
        以及每个通道对应的 ``{name}_valid`` 有效性掩码列。

    Raises:
        TcpStateProbeError: 输入缺少必需列，或同一窗口内的分组键取值不
            一致（数据契约被破坏）。
    """
    required = {*JOIN_KEYS, *_GROUP_KEY_COLUMNS, "sender_index"}
    for spec in TCP_STATE_CHANNEL_SPECS:
        required.add(spec.value_col)
        required.add(spec.mask_col)
        if spec.weight_col is not None:
            required.add(spec.weight_col)
    missing = sorted(required - set(tcp_frame.columns))
    if missing:
        raise TcpStateProbeError(f"TCP 发送者真值表缺少必需列：{missing}")

    key_check = tcp_frame.groupby(list(JOIN_KEYS), sort=False)[list(_GROUP_KEY_COLUMNS)].nunique()
    if bool((key_check > 1).to_numpy().any()):
        raise TcpStateProbeError("同一窗口内分组键取值不一致，数据契约被破坏")

    join_key_series = [tcp_frame[key] for key in JOIN_KEYS]
    result = tcp_frame.groupby(list(JOIN_KEYS), sort=False)[list(_GROUP_KEY_COLUMNS)].first()

    for spec in TCP_STATE_CHANNEL_SPECS:
        mask = tcp_frame[spec.mask_col].astype(bool)
        values = pd.to_numeric(tcp_frame[spec.value_col], errors="raise")
        if spec.unset_sentinel is not None:
            mask = mask & (values != spec.unset_sentinel)

        if spec.kind == "weighted_mean":
            if spec.weight_col is None:
                raise TcpStateProbeError(f"通道 {spec.name} 缺少权重列配置")
            weight = pd.to_numeric(tcp_frame[spec.weight_col], errors="raise")
            if bool((weight < 0).any()):
                raise TcpStateProbeError(f"权重列 {spec.weight_col} 出现负值")
            effective_weight = weight.where(mask, 0.0)
            numerator = (values * effective_weight).groupby(join_key_series).sum()
            denominator = effective_weight.groupby(join_key_series).sum()
            valid = denominator > 0
            aggregated = (numerator / denominator.where(valid, 1.0)).where(valid, np.nan)
            result[spec.name] = aggregated
            result[f"{spec.name}_valid"] = valid
        else:
            masked_values = values.where(mask)
            sum_series = masked_values.groupby(join_key_series).sum(min_count=1)
            mean_series = masked_values.groupby(join_key_series).mean()
            observed_count = mask.groupby(join_key_series).sum()
            valid = observed_count > 0
            result[f"{spec.name}_sum"] = sum_series
            result[f"{spec.name}_mean"] = mean_series
            result[f"{spec.name}_valid"] = valid

    return result.reset_index()


def compute_target_frame(e2_frame: pd.DataFrame, tcp_frame: pd.DataFrame) -> pd.DataFrame:
    """构造 D1/D2/V1/V2/V3 共用的窗口级分析表：train-fit + TCP，七字段与状态通道对齐。

    Args:
        e2_frame: e2-physics-auxiliary-v1 制品（逐窗口一行，含七字段）。
        tcp_frame: tcp-sender-truth-v2 制品（逐窗口 8 发送者一行）。

    Returns:
        窗口级 DataFrame，含 JOIN_KEYS、_GROUP_KEY_COLUMNS、
        _WINDOW_ORDER_COLUMN（场景内窗口序号，供 V2 按窗口序号切分使用）、
        FEATURE_COLUMNS 与 state_channel_output_columns() 及其 ``_valid``
        掩码列。

    Raises:
        TcpStateProbeError: 两份制品在 train-fit + TCP 子集上按窗口键未能
            一一对齐，或聚合后的传输族出现非 TCP 行。
    """
    missing_e2 = sorted(
        {
            "split_id",
            "transport_family",
            _WINDOW_ORDER_COLUMN,
            *JOIN_KEYS,
            *FEATURE_COLUMNS,
        }
        - set(e2_frame.columns)
    )
    if missing_e2:
        raise TcpStateProbeError(f"e2 物理辅助制品缺少必需列：{missing_e2}")

    e2_subset = e2_frame[
        (e2_frame["split_id"] == TRAIN_FIT_SPLIT_ID)
        & (e2_frame["transport_family"] == TCP_TRANSPORT_FAMILY)
    ]
    e2_features = e2_subset[
        [*JOIN_KEYS, _WINDOW_ORDER_COLUMN, *FEATURE_COLUMNS]
    ].copy()

    tcp_train_fit = tcp_frame[tcp_frame["split_id"] == TRAIN_FIT_SPLIT_ID]
    aggregated = aggregate_tcp_state_channels(tcp_train_fit)
    if not bool((aggregated["transport_family"] == TCP_TRANSPORT_FAMILY).all()):
        raise TcpStateProbeError("tcp-sender-truth-v2 train-fit 子集出现非 TCP 行")

    merged = e2_features.merge(aggregated, on=list(JOIN_KEYS), how="inner", validate="one_to_one")
    if len(merged) != len(e2_features) or len(merged) != len(aggregated):
        raise TcpStateProbeError("七字段表与 TCP 状态聚合表按窗口键未能一一对齐")
    return merged


# ---------------------------------------------------------------------------
# D1：状态目标非退化与置换分辨力。
# ---------------------------------------------------------------------------


def _derangement(n: int, rng: np.random.Generator) -> np.ndarray:
    """生成长度为 n 的无固定点置换（拒绝采样，n >= 2）。

    Args:
        n: 待置换元素数量。
        rng: 已按 RANDOM_SEED 播种的随机数生成器。

    Returns:
        长度为 n 的整数索引数组，满足 permuted[i] != i 对全部 i 成立。

    Raises:
        TcpStateProbeError: n < 2 时无固定点置换不存在。
    """
    if n < 2:
        raise TcpStateProbeError("无固定点置换要求元素数量至少为 2")
    identity = np.arange(n)
    while True:
        candidate = rng.permutation(n)
        if not bool(np.any(candidate == identity)):
            return candidate


def compute_dynamics_evidence(tcp_train_fit_frame: pd.DataFrame) -> dict[str, object]:
    """D1 项 4：cwnd 窗口净变化非零，或丢包事件计数 > 0 的窗口比例。

    cwnd 变化按窗口级求和口径判定（与 sum_and_mean 通道一致）：只要求和
    值在有效观测下发生变化即计入；丢包事件计数无观测掩码列（恒为已观测），
    直接对全部发送者求和后判断是否大于零。

    Args:
        tcp_train_fit_frame: 已限定 split_id == train-fit 的发送者级真值表。

    Returns:
        字典，含 windows_total、cwnd_changed_ratio、loss_event_ratio、
        combined_ratio、passed。
    """
    join_key_series = [tcp_train_fit_frame[key] for key in JOIN_KEYS]
    cwnd_start_mask = tcp_train_fit_frame["cwnd_start_observed"].astype(bool)
    cwnd_end_mask = tcp_train_fit_frame["cwnd_end_observed"].astype(bool)
    cwnd_start_masked = tcp_train_fit_frame["truth_tcp_cwnd_start_bytes"].where(cwnd_start_mask)
    cwnd_end_masked = tcp_train_fit_frame["truth_tcp_cwnd_end_bytes"].where(cwnd_end_mask)
    cwnd_start_sum = cwnd_start_masked.groupby(join_key_series).sum(min_count=1)
    cwnd_end_sum = cwnd_end_masked.groupby(join_key_series).sum(min_count=1)
    loss_sum = tcp_train_fit_frame["truth_tcp_loss_event_count"].groupby(join_key_series).sum()

    both_valid = cwnd_start_sum.notna() & cwnd_end_sum.notna()
    cwnd_changed = (
        ((cwnd_end_sum != cwnd_start_sum) & both_valid).reindex(loss_sum.index).fillna(False)
    )
    has_loss = loss_sum > 0
    combined = cwnd_changed | has_loss

    windows_total = int(len(loss_sum))
    ratio = float(combined.mean())
    return {
        "windows_total": windows_total,
        "cwnd_changed_ratio": float(cwnd_changed.mean()),
        "loss_event_ratio": float(has_loss.mean()),
        "combined_ratio": ratio,
        "passed": ratio >= MIN_DYNAMICS_EVIDENCE_WINDOW_RATIO,
    }


def run_d1(merged: pd.DataFrame, tcp_train_fit_frame: pd.DataFrame) -> dict[str, object]:
    """执行 D1 四项判据，逐通道逐项报告，任一失败即整体不通过。

    Args:
        merged: compute_target_frame 的输出。
        tcp_train_fit_frame: 已限定 split_id == train-fit 的发送者级真值表，
            供项 4 动力学证据计算使用。

    Returns:
        字典，含 per_channel（逐通道逐项结果）、item4_dynamics_evidence、
        failed_items（未通过的「通道:项」标识列表）、passed。

    Raises:
        TcpStateProbeError: 某通道有效值全部相同（标准差为零，无法 z
            标准化），说明该通道已彻底退化。
    """
    channel_columns = state_channel_output_columns()
    rng = np.random.default_rng(RANDOM_SEED)
    strata = merged["evaluation_cluster_id"].to_numpy()

    per_channel: dict[str, dict[str, object]] = {}
    failed_items: list[str] = []
    overall_passed = True

    for column in channel_columns:
        valid_column = _channel_valid_column(column)
        valid_mask = merged[valid_column].astype(bool).to_numpy()
        valid_ratio = float(valid_mask.mean())

        raw = merged[column].to_numpy(dtype=float)
        valid_values = raw[valid_mask]
        mean = float(np.mean(valid_values))
        std = float(np.std(valid_values, ddof=0))
        if std <= 0.0:
            raise TcpStateProbeError(f"通道 {column} 有效值标准差为零，无法 z 标准化")
        z_scores = np.full(raw.shape[0], np.nan)
        z_scores[valid_mask] = (valid_values - mean) / std

        stratum_stds: list[float] = []
        permutation_abs_deltas: list[np.ndarray] = []
        for stratum_id in pd.unique(strata):
            stratum_idx = np.where((strata == stratum_id) & valid_mask)[0]
            if stratum_idx.size < 2:
                continue
            stratum_z = z_scores[stratum_idx]
            stratum_stds.append(float(np.std(stratum_z, ddof=0)))
            permutation = _derangement(stratum_idx.size, rng)
            permutation_abs_deltas.append(np.abs(stratum_z[permutation] - stratum_z))

        stratum_std_median = float(np.median(stratum_stds)) if stratum_stds else float("nan")
        permutation_mean_abs_delta = (
            float(np.mean(np.concatenate(permutation_abs_deltas)))
            if permutation_abs_deltas
            else float("nan")
        )

        item1_passed = valid_ratio >= MIN_OBSERVED_VALID_RATIO
        item2_passed = stratum_std_median >= MIN_STRATUM_TARGET_STD_MEDIAN_Z
        item3_passed = permutation_mean_abs_delta >= MIN_PERMUTATION_MEAN_ABS_DELTA_Z

        per_channel[column] = {
            "valid_ratio": valid_ratio,
            "item1_valid_ratio_passed": item1_passed,
            "stratum_std_median_z": stratum_std_median,
            "item2_stratum_std_passed": item2_passed,
            "n_strata_used": len(stratum_stds),
            "permutation_mean_abs_delta_z": permutation_mean_abs_delta,
            "item3_permutation_passed": item3_passed,
        }
        if not item1_passed:
            failed_items.append(f"{column}:item1_valid_ratio")
            overall_passed = False
        if not item2_passed:
            failed_items.append(f"{column}:item2_stratum_std")
            overall_passed = False
        if not item3_passed:
            failed_items.append(f"{column}:item3_permutation")
            overall_passed = False

    dynamics = compute_dynamics_evidence(tcp_train_fit_frame)
    if not bool(dynamics["passed"]):
        failed_items.append("item4_dynamics_evidence")
        overall_passed = False

    return {
        "per_channel": per_channel,
        "item4_dynamics_evidence": dynamics,
        "failed_items": failed_items,
        "passed": overall_passed,
    }


# ---------------------------------------------------------------------------
# D2：可预测性探针（分组交叉验证 R²）。
# ---------------------------------------------------------------------------


def _select_ridge_alpha(features: np.ndarray, target: np.ndarray, groups: np.ndarray) -> float:
    """在训练折内部用分组交叉验证从 RIDGE_ALPHA_GRID 选出最优 alpha。

    Args:
        features: 已标准化的训练折特征矩阵。
        target: 已标准化的训练折目标向量。
        groups: 训练折样本的分组键（physics_group_sha256）。

    Returns:
        RIDGE_ALPHA_GRID 中平均验证 R² 最高的 alpha；训练折内分组数不足
        以支持 2 折内层交叉验证时退化为网格中的最小 alpha。
    """
    n_groups = int(np.unique(groups).size)
    inner_splits = min(RIDGE_INNER_FOLDS, n_groups)
    if inner_splits < 2:
        logger.warning("训练折内分组数=%d 不足以做内层交叉验证，退化为最小 alpha", n_groups)
        return RIDGE_ALPHA_GRID[0]

    inner_cv = GroupKFold(n_splits=inner_splits)
    scores: dict[float, list[float]] = {alpha: [] for alpha in RIDGE_ALPHA_GRID}
    for train_idx, val_idx in inner_cv.split(features, target, groups):
        for alpha in RIDGE_ALPHA_GRID:
            model = Ridge(alpha=alpha, random_state=RANDOM_SEED)
            model.fit(features[train_idx], target[train_idx])
            prediction = model.predict(features[val_idx])
            scores[alpha].append(float(r2_score(target[val_idx], prediction)))
    mean_scores = {alpha: float(np.mean(values)) for alpha, values in scores.items()}
    return max(mean_scores, key=lambda alpha: mean_scores[alpha])


def _grouped_cv_r2_ridge(
    features: np.ndarray, target: np.ndarray, groups: np.ndarray
) -> tuple[float, list[float], list[float]]:
    """岭回归的外层分组五折交叉验证，报告折外（OOF）合并 R²。

    Returns:
        (pooled_oof_r2, per_fold_r2, selected_alpha_per_fold)。
    """
    outer_cv = GroupKFold(n_splits=N_GROUP_FOLDS)
    oof_prediction = np.full_like(target, fill_value=np.nan, dtype=float)
    fold_r2: list[float] = []
    fold_alpha: list[float] = []

    for train_idx, test_idx in outer_cv.split(features, target, groups):
        x_scaler = StandardScaler().fit(features[train_idx])
        y_scaler = StandardScaler().fit(target[train_idx].reshape(-1, 1))
        x_train_scaled = x_scaler.transform(features[train_idx])
        x_test_scaled = x_scaler.transform(features[test_idx])
        y_train_scaled = y_scaler.transform(target[train_idx].reshape(-1, 1)).ravel()

        best_alpha = _select_ridge_alpha(x_train_scaled, y_train_scaled, groups[train_idx])
        model = Ridge(alpha=best_alpha, random_state=RANDOM_SEED)
        model.fit(x_train_scaled, y_train_scaled)
        prediction_scaled = model.predict(x_test_scaled)
        prediction = y_scaler.inverse_transform(prediction_scaled.reshape(-1, 1)).ravel()

        oof_prediction[test_idx] = prediction
        fold_r2.append(float(r2_score(target[test_idx], prediction)))
        fold_alpha.append(best_alpha)

    pooled_r2 = float(r2_score(target, oof_prediction))
    return pooled_r2, fold_r2, fold_alpha


def _grouped_cv_r2_mlp(
    features: np.ndarray, target: np.ndarray, groups: np.ndarray
) -> tuple[float, list[float]]:
    """两层 MLP（早停）的外层分组五折交叉验证，报告折外（OOF）合并 R²。

    Returns:
        (pooled_oof_r2, per_fold_r2)。
    """
    outer_cv = GroupKFold(n_splits=N_GROUP_FOLDS)
    oof_prediction = np.full_like(target, fill_value=np.nan, dtype=float)
    fold_r2: list[float] = []

    for train_idx, test_idx in outer_cv.split(features, target, groups):
        x_scaler = StandardScaler().fit(features[train_idx])
        y_scaler = StandardScaler().fit(target[train_idx].reshape(-1, 1))
        x_train_scaled = x_scaler.transform(features[train_idx])
        x_test_scaled = x_scaler.transform(features[test_idx])
        y_train_scaled = y_scaler.transform(target[train_idx].reshape(-1, 1)).ravel()

        model = MLPRegressor(
            hidden_layer_sizes=MLP_HIDDEN_LAYER_SIZES,
            max_iter=MLP_MAX_ITER,
            early_stopping=True,
            validation_fraction=MLP_VALIDATION_FRACTION,
            n_iter_no_change=MLP_N_ITER_NO_CHANGE,
            random_state=RANDOM_SEED,
        )
        model.fit(x_train_scaled, y_train_scaled)
        prediction_scaled = model.predict(x_test_scaled)
        prediction = y_scaler.inverse_transform(prediction_scaled.reshape(-1, 1)).ravel()

        oof_prediction[test_idx] = prediction
        fold_r2.append(float(r2_score(target[test_idx], prediction)))

    pooled_r2 = float(r2_score(target, oof_prediction))
    return pooled_r2, fold_r2


def run_d2(merged: pd.DataFrame) -> dict[str, object]:
    """执行 D2：逐通道逐模型分组交叉验证 R²，并按预注册判据裁决。

    Args:
        merged: compute_target_frame 的输出。

    Returns:
        字典，含 per_channel（逐通道岭回归/MLP 折外 R² 与折内明细）、
        best_channel、best_model、best_r2、
        all_below_degenerate_threshold、near_deterministic_warning、verdict。

    Raises:
        TcpStateProbeError: 某通道有效样本覆盖的物理组数不足 N_GROUP_FOLDS，
            无法做五折分组交叉验证。
    """
    channel_columns = state_channel_output_columns()
    feature_matrix = merged[list(FEATURE_COLUMNS)].to_numpy(dtype=float)
    group_keys = merged["physics_group_sha256"].to_numpy()

    per_channel: dict[str, dict[str, object]] = {}
    best_channel: str | None = None
    best_model: str | None = None
    best_r2 = float("-inf")

    for column in channel_columns:
        valid_column = _channel_valid_column(column)
        valid_mask = merged[valid_column].astype(bool).to_numpy()
        target = merged[column].to_numpy(dtype=float)[valid_mask]
        features = feature_matrix[valid_mask]
        groups = group_keys[valid_mask]
        n_valid = int(valid_mask.sum())

        n_groups = int(np.unique(groups).size)
        if n_groups < N_GROUP_FOLDS:
            raise TcpStateProbeError(
                f"通道 {column} 有效样本覆盖的物理组数={n_groups} 不足 {N_GROUP_FOLDS} 折"
            )

        ridge_r2, ridge_fold_r2, ridge_fold_alpha = _grouped_cv_r2_ridge(features, target, groups)
        mlp_r2, mlp_fold_r2 = _grouped_cv_r2_mlp(features, target, groups)

        per_channel[column] = {
            "n_valid": n_valid,
            "ridge": {
                "pooled_oof_r2": ridge_r2,
                "fold_r2": ridge_fold_r2,
                "fold_alpha": ridge_fold_alpha,
            },
            "mlp": {
                "pooled_oof_r2": mlp_r2,
                "fold_r2": mlp_fold_r2,
            },
        }
        for model_name, r2_value in (("ridge", ridge_r2), ("mlp", mlp_r2)):
            if r2_value > best_r2:
                best_r2 = r2_value
                best_channel = column
                best_model = model_name

    all_r2 = [entry["ridge"]["pooled_oof_r2"] for entry in per_channel.values()] + [
        entry["mlp"]["pooled_oof_r2"] for entry in per_channel.values()
    ]
    all_below_degenerate = all(value < D2_DEGENERATE_R2_THRESHOLD for value in all_r2)
    near_deterministic = best_r2 > D2_NEAR_DETERMINISTIC_R2_THRESHOLD

    if all_below_degenerate:
        verdict = "rejected"
    elif near_deterministic:
        verdict = "passed_with_near_deterministic_warning"
    else:
        verdict = "passed"

    return {
        "per_channel": per_channel,
        "best_channel": best_channel,
        "best_model": best_model,
        "best_r2": float(best_r2),
        "all_below_degenerate_threshold": all_below_degenerate,
        "near_deterministic_warning": near_deterministic,
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# V1/V2/V3 共用辅助函数：分组均值广播与组内中心化。
# ---------------------------------------------------------------------------


def _group_mean_broadcast(values: np.ndarray, groups: np.ndarray) -> np.ndarray:
    """按 groups 分组，把 values 逐行替换为其所属分组的组内均值，形状不变。

    一维输入（如目标向量）与二维输入（如特征矩阵，行是样本、列是特征）都
    支持，二维时逐列分别计算组内均值。

    Args:
        values: 形状为 (n,) 或 (n, k) 的数值数组。
        groups: 长度为 n 的分组键数组，与 values 逐行对应。

    Returns:
        与 values 同形状的数组；第 i 行是 groups[i] 所属分组的（逐列）均值。
    """
    original_ndim = values.ndim
    frame = pd.DataFrame(values if original_ndim == 2 else values.reshape(-1, 1))
    group_index = pd.Index(groups, name="group")
    group_means = frame.groupby(group_index).transform("mean").to_numpy()
    return group_means if original_ndim == 2 else group_means.ravel()


def _center_within_group(values: np.ndarray, groups: np.ndarray) -> np.ndarray:
    """把 values 逐行减去其所属分组（groups）的组内均值，实现组内中心化。

    供 V1 使用：目标与七字段特征都要用同一分组键（evaluation_cluster_id）
    中心化，若只中心化目标而不中心化特征，场景身份会从特征侧漏回来，
    R²_within 会被人为拉高，结论失效。

    Args:
        values: 形状为 (n,) 或 (n, k) 的数值数组。
        groups: 长度为 n 的分组键数组。

    Returns:
        与 values 同形状的组内中心化结果，每个分组内的均值精确为零。
    """
    return values - _group_mean_broadcast(values, groups)


# ---------------------------------------------------------------------------
# V1：场景中心化可预测性（决定性）。
# ---------------------------------------------------------------------------


def run_v1(merged: pd.DataFrame) -> dict[str, object]:
    """执行 V1：逐通道计算场景中心化折外 R²_within 与场景指纹对照 R²_between。

    目标与七字段特征都先减去所属 evaluation_cluster_id 的组内均值（双侧
    中心化，见 _center_within_group），再按 physics_group_sha256 分组五折
    交叉验证，取岭回归与 MLP 折外 R² 中较大者为 R²_within（更保守：只要
    任一模型能从场景内残差中学出信号即视为未退化）。对照 R²_between 用
    「所属场景七字段组内均值」（不随窗口变化的场景指纹）作特征，去预测
    原始未中心化目标，同样取两模型中较大者，衡量仅凭场景身份能解释多少
    原始方差。

    Args:
        merged: compute_target_frame 的输出。

    Returns:
        字典，含 per_channel（逐通道 R²_within/R²_between 明细与逐通道
        裁决）、reject_channels、strong_form_channels、uncertain_channels、
        verdict（"route_closed" | "narrow_gate_retained" | "uncertain"）。

    Raises:
        TcpStateProbeError: 某通道有效样本覆盖的场景数不足 N_GROUP_FOLDS，
            无法做五折分组交叉验证。
    """
    channel_columns = state_channel_output_columns()
    feature_matrix = merged[list(FEATURE_COLUMNS)].to_numpy(dtype=float)
    cluster_keys = merged["evaluation_cluster_id"].to_numpy()
    group_keys = merged["physics_group_sha256"].to_numpy()

    per_channel: dict[str, dict[str, object]] = {}
    reject_channels: list[str] = []
    strong_form_channels: list[str] = []
    uncertain_channels: list[str] = []

    for column in channel_columns:
        valid_column = _channel_valid_column(column)
        valid_mask = merged[valid_column].astype(bool).to_numpy()
        n_valid = int(valid_mask.sum())

        target_raw = merged[column].to_numpy(dtype=float)[valid_mask]
        features_raw = feature_matrix[valid_mask]
        clusters_valid = cluster_keys[valid_mask]
        groups_valid = group_keys[valid_mask]

        n_groups = int(np.unique(groups_valid).size)
        if n_groups < N_GROUP_FOLDS:
            raise TcpStateProbeError(
                f"V1 通道 {column} 有效样本覆盖的物理组数={n_groups} 不足 {N_GROUP_FOLDS} 折"
            )

        # 双侧中心化：目标与七字段特征都减去所属场景（evaluation_cluster_id）
        # 的组内均值，避免场景身份从特征侧漏回来。
        target_centered = _center_within_group(target_raw, clusters_valid)
        features_centered = _center_within_group(features_raw, clusters_valid)

        ridge_within_r2, ridge_within_fold_r2, _ = _grouped_cv_r2_ridge(
            features_centered, target_centered, groups_valid
        )
        mlp_within_r2, mlp_within_fold_r2 = _grouped_cv_r2_mlp(
            features_centered, target_centered, groups_valid
        )
        within_r2 = max(ridge_within_r2, mlp_within_r2)

        # 对照：只用所属场景七字段组内均值（场景指纹，行内不随窗口变化）
        # 预测原始未中心化目标。
        cluster_mean_features = _group_mean_broadcast(features_raw, clusters_valid)
        ridge_between_r2, ridge_between_fold_r2, _ = _grouped_cv_r2_ridge(
            cluster_mean_features, target_raw, groups_valid
        )
        mlp_between_r2, mlp_between_fold_r2 = _grouped_cv_r2_mlp(
            cluster_mean_features, target_raw, groups_valid
        )
        between_r2 = max(ridge_between_r2, mlp_between_r2)

        channel_reject = within_r2 >= V1_WITHIN_R2_REJECT_THRESHOLD
        channel_strong_form = (
            within_r2 < V1_WITHIN_R2_STRONG_FORM_THRESHOLD
            and between_r2 >= V1_BETWEEN_R2_STRONG_FORM_THRESHOLD
        )

        per_channel[column] = {
            "n_valid": n_valid,
            "within_r2_ridge": ridge_within_r2,
            "within_r2_mlp": mlp_within_r2,
            "within_r2_max": within_r2,
            "within_fold_r2_ridge": ridge_within_fold_r2,
            "within_fold_r2_mlp": mlp_within_fold_r2,
            "between_r2_ridge": ridge_between_r2,
            "between_r2_mlp": mlp_between_r2,
            "between_r2_max": between_r2,
            "between_fold_r2_ridge": ridge_between_fold_r2,
            "between_fold_r2_mlp": mlp_between_fold_r2,
            "reject_channel": channel_reject,
            "strong_form_channel": channel_strong_form,
        }
        if channel_reject:
            reject_channels.append(column)
        elif channel_strong_form:
            strong_form_channels.append(column)
        else:
            uncertain_channels.append(column)

    if reject_channels:
        verdict = "narrow_gate_retained"
    elif len(strong_form_channels) == len(channel_columns):
        verdict = "route_closed"
    else:
        verdict = "uncertain"

    return {
        "per_channel": per_channel,
        "reject_channels": reject_channels,
        "strong_form_channels": strong_form_channels,
        "uncertain_channels": uncertain_channels,
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# V2：场景可分性探针。
# ---------------------------------------------------------------------------


def _prepare_v2_window_split(window_index: np.ndarray, cluster_ids: np.ndarray) -> np.ndarray:
    """按场景内窗口序号（非随机）切分训练/测试掩码。

    每个 evaluation_cluster_id 内取前 V2_TRAIN_WINDOW_FRACTION 比例的
    source_window_index 作训练，其余作测试；用统一的全局阈值切分要求
    各场景内窗口序号取值范围一致，否则同一阈值无法保证跨场景比例一致。

    Args:
        window_index: 每行的场景内窗口序号（source_window_index）。
        cluster_ids: 每行所属的 evaluation_cluster_id。

    Returns:
        布尔数组，True 表示该行划入训练集。

    Raises:
        TcpStateProbeError: 各 evaluation_cluster_id 内 window_index 的
            最小值或最大值不一致。
    """
    frame = pd.DataFrame({"window_index": window_index, "cluster": cluster_ids})
    cluster_min = frame.groupby("cluster")["window_index"].min()
    cluster_max = frame.groupby("cluster")["window_index"].max()
    if cluster_min.nunique() != 1 or cluster_max.nunique() != 1:
        raise TcpStateProbeError(
            "evaluation_cluster_id 之间 source_window_index 范围不一致，无法用统一阈值切分"
        )
    window_count = int(cluster_max.iloc[0]) - int(cluster_min.iloc[0]) + 1
    split_threshold = int(cluster_min.iloc[0]) + int(
        np.floor(V2_TRAIN_WINDOW_FRACTION * window_count)
    )
    return window_index < split_threshold


def _fit_predict_top1_accuracy(
    x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray, y_test: np.ndarray
) -> dict[str, float]:
    """特征标准化（按训练折统计量）后，分别用逻辑回归与随机森林分类。

    标准化器只在训练集上拟合，避免测试集统计量泄漏到训练阶段。

    Args:
        x_train: 训练集特征矩阵。
        y_train: 训练集标签（evaluation_cluster_id）。
        x_test: 测试集特征矩阵。
        y_test: 测试集标签。

    Returns:
        字典，含 logistic_regression_top1_accuracy、
        random_forest_top1_accuracy、top1_accuracy_max。
    """
    scaler = StandardScaler().fit(x_train)
    x_train_scaled = scaler.transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    logistic = LogisticRegression(
        max_iter=V2_LOGISTIC_REGRESSION_MAX_ITER, random_state=RANDOM_SEED
    )
    logistic.fit(x_train_scaled, y_train)
    logistic_accuracy = float(accuracy_score(y_test, logistic.predict(x_test_scaled)))

    forest = RandomForestClassifier(
        n_estimators=V2_RANDOM_FOREST_N_ESTIMATORS, random_state=RANDOM_SEED, n_jobs=-1
    )
    forest.fit(x_train_scaled, y_train)
    forest_accuracy = float(accuracy_score(y_test, forest.predict(x_test_scaled)))

    return {
        "logistic_regression_top1_accuracy": logistic_accuracy,
        "random_forest_top1_accuracy": forest_accuracy,
        "top1_accuracy_max": max(logistic_accuracy, forest_accuracy),
    }


def run_v2(merged: pd.DataFrame) -> dict[str, object]:
    """执行 V2：用七字段与状态目标分别分类 128 个 evaluation_cluster_id。

    按场景内窗口序号（非随机）切分训练/测试，避免同场景相邻窗口跨集合
    泄漏。七字段分类回答「七字段本身是否强编码场景身份」；状态目标分类
    （只用全部通道都有效观测的窗口）回答「状态是否接近场景 ID 的确定
    函数」。

    Args:
        merged: compute_target_frame 的输出。

    Returns:
        字典，含 chance_level_top1_accuracy、训练/测试窗口数、
        field_based（七字段分类结果与 passed_strong_encoding 判定）、
        state_based（状态目标分类结果与 near_perfect 判定）、verdict。
    """
    window_index = merged[_WINDOW_ORDER_COLUMN].to_numpy()
    cluster_ids = merged["evaluation_cluster_id"].to_numpy()
    train_mask = _prepare_v2_window_split(window_index, cluster_ids)

    field_matrix = merged[list(FEATURE_COLUMNS)].to_numpy(dtype=float)
    field_result = _fit_predict_top1_accuracy(
        field_matrix[train_mask],
        cluster_ids[train_mask],
        field_matrix[~train_mask],
        cluster_ids[~train_mask],
    )

    channel_columns = state_channel_output_columns()
    all_valid_mask = np.ones(len(merged), dtype=bool)
    for column in channel_columns:
        all_valid_mask &= merged[_channel_valid_column(column)].astype(bool).to_numpy()

    state_matrix = merged[list(channel_columns)].to_numpy(dtype=float)[all_valid_mask]
    state_cluster_ids = cluster_ids[all_valid_mask]
    state_train_mask = train_mask[all_valid_mask]
    n_state_valid = int(all_valid_mask.sum())

    state_result = _fit_predict_top1_accuracy(
        state_matrix[state_train_mask],
        state_cluster_ids[state_train_mask],
        state_matrix[~state_train_mask],
        state_cluster_ids[~state_train_mask],
    )

    field_passed = field_result["top1_accuracy_max"] >= V2_FIELD_TOP1_ACCURACY_THRESHOLD
    state_near_perfect = (
        state_result["top1_accuracy_max"] >= V2_STATE_NEAR_PERFECT_TOP1_ACCURACY_THRESHOLD
    )

    return {
        "chance_level_top1_accuracy": V2_CHANCE_LEVEL_TOP1_ACCURACY,
        "n_train_windows": int(train_mask.sum()),
        "n_test_windows": int((~train_mask).sum()),
        "field_based": {**field_result, "passed_strong_encoding": field_passed},
        "state_based": {
            **state_result,
            "n_valid_windows": n_state_valid,
            "n_train_windows": int(state_train_mask.sum()),
            "n_test_windows": int((~state_train_mask).sum()),
            "near_perfect": state_near_perfect,
        },
        "verdict": "scene_strongly_encoded" if field_passed else "not_strongly_encoded",
    }


# ---------------------------------------------------------------------------
# V3：动态量方差分解。
# ---------------------------------------------------------------------------


def _between_within_variance_ratio(values: np.ndarray, groups: np.ndarray) -> dict[str, float]:
    """按分组计算场景间方差（组均值的方差）与场景内方差（组内方差的均值）之比。

    与背景事实「128 个 evaluation_cluster_id 之间的方差约为场景内方差的
    70 倍」使用同一口径：组间方差 = Var(各组均值)（ddof=0），组内方差 =
    各组内部方差（ddof=0）的未加权均值，比值 = 组间方差 / 组内方差。

    Args:
        values: 待分解的数值数组。
        groups: 与 values 逐行对应的分组键（evaluation_cluster_id）。

    Returns:
        字典，含 between_variance、within_variance、ratio、n_groups。

    Raises:
        TcpStateProbeError: 组内方差为零（全部组内部完全无变化），比值退化。
    """
    frame = pd.DataFrame({"value": values, "group": groups})
    group_means = frame.groupby("group")["value"].mean()
    group_vars = frame.groupby("group")["value"].var(ddof=0)
    between_variance = float(group_means.var(ddof=0))
    within_variance = float(group_vars.mean())
    if within_variance <= 0.0:
        raise TcpStateProbeError("组内方差为零，场景间/场景内方差比退化")
    return {
        "between_variance": between_variance,
        "within_variance": within_variance,
        "ratio": between_variance / within_variance,
        "n_groups": int(group_means.shape[0]),
    }


def compute_v3_dynamics_frame(tcp_train_fit_frame: pd.DataFrame) -> pd.DataFrame:
    """把逐发送者 TCP 真值折叠为窗口级三个动态量。

    三个动态量：cwnd 窗口净变化（求和口径的 end - start，与 D1 项 4 一致，
    只保留起止值均有效观测的窗口）、truth_tcp_loss_event_count 窗口内求和
    （无观测掩码列，恒为已观测）、truth_tcp_cwnd_contraction_event_count
    窗口内求和（同样无观测掩码列）。

    Args:
        tcp_train_fit_frame: 已限定 split_id == train-fit 的发送者级真值表。

    Returns:
        DataFrame，每行对应一个窗口，含 evaluation_cluster_id 及
        cwnd_net_change_bytes、loss_event_count、cwnd_contraction_event_count
        三列；cwnd_net_change_bytes 在起止值任一未观测时为 NaN。

    Raises:
        TcpStateProbeError: 输入缺少必需列。
    """
    required = {
        *JOIN_KEYS,
        "evaluation_cluster_id",
        "cwnd_start_observed",
        "cwnd_end_observed",
        "truth_tcp_cwnd_start_bytes",
        "truth_tcp_cwnd_end_bytes",
        "truth_tcp_loss_event_count",
        "truth_tcp_cwnd_contraction_event_count",
    }
    missing = sorted(required - set(tcp_train_fit_frame.columns))
    if missing:
        raise TcpStateProbeError(f"V3 动态量计算缺少必需列：{missing}")

    join_key_series = [tcp_train_fit_frame[key] for key in JOIN_KEYS]
    cluster_ids = tcp_train_fit_frame.groupby(join_key_series, sort=False)[
        "evaluation_cluster_id"
    ].first()

    start_mask = tcp_train_fit_frame["cwnd_start_observed"].astype(bool)
    end_mask = tcp_train_fit_frame["cwnd_end_observed"].astype(bool)
    start_sum = (
        tcp_train_fit_frame["truth_tcp_cwnd_start_bytes"]
        .where(start_mask)
        .groupby(join_key_series)
        .sum(min_count=1)
    )
    end_sum = (
        tcp_train_fit_frame["truth_tcp_cwnd_end_bytes"]
        .where(end_mask)
        .groupby(join_key_series)
        .sum(min_count=1)
    )
    cwnd_net_change = end_sum - start_sum

    loss_sum = tcp_train_fit_frame["truth_tcp_loss_event_count"].groupby(join_key_series).sum()
    contraction_sum = (
        tcp_train_fit_frame["truth_tcp_cwnd_contraction_event_count"]
        .groupby(join_key_series)
        .sum()
    )

    result = pd.DataFrame(
        {
            "evaluation_cluster_id": cluster_ids,
            "cwnd_net_change_bytes": cwnd_net_change,
            "loss_event_count": loss_sum,
            "cwnd_contraction_event_count": contraction_sum,
        }
    ).reset_index()
    return result


#: V3 待分解的三个动态量列名，按 compute_v3_dynamics_frame 的输出列命名。
V3_DYNAMICS_QUANTITIES: tuple[str, ...] = (
    "cwnd_net_change_bytes",
    "loss_event_count",
    "cwnd_contraction_event_count",
)


def run_v3(tcp_train_fit_frame: pd.DataFrame) -> dict[str, object]:
    """执行 V3：对三个窗口动态量重复 D1 式的场景间/场景内方差分解。

    Args:
        tcp_train_fit_frame: 已限定 split_id == train-fit 的发送者级真值表。

    Returns:
        字典，含 per_quantity（逐动态量的方差分解与逐量裁决）、
        all_not_dominated_by_scene、any_strong_form_confirmed。
    """
    dynamics_frame = compute_v3_dynamics_frame(tcp_train_fit_frame)

    per_quantity: dict[str, dict[str, object]] = {}
    for quantity in V3_DYNAMICS_QUANTITIES:
        valid = dynamics_frame[quantity].notna().to_numpy()
        values = dynamics_frame[quantity].to_numpy(dtype=float)[valid]
        groups = dynamics_frame["evaluation_cluster_id"].to_numpy()[valid]
        stats = _between_within_variance_ratio(values, groups)
        not_dominated = stats["ratio"] < V3_DYNAMICS_NOT_DOMINATED_RATIO_THRESHOLD
        strong_form = stats["ratio"] >= V3_DYNAMICS_STRONG_FORM_RATIO_THRESHOLD
        per_quantity[quantity] = {
            **stats,
            "n_windows_valid": int(valid.sum()),
            "not_dominated_by_scene": not_dominated,
            "strong_form_confirmed": strong_form,
        }

    all_not_dominated = all(bool(v["not_dominated_by_scene"]) for v in per_quantity.values())
    any_strong_form = any(bool(v["strong_form_confirmed"]) for v in per_quantity.values())

    return {
        "per_quantity": per_quantity,
        "all_not_dominated_by_scene": all_not_dominated,
        "any_strong_form_confirmed": any_strong_form,
    }


# ---------------------------------------------------------------------------
# 命令行入口。
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。

    仅暴露数据路径、运行范围与输出路径参数；全部判据阈值、随机种子、
    交叉验证折数与模型超参数均为模块级冻结常量，不提供命令行覆盖入口。
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--e2-path",
        type=Path,
        default=DEFAULT_E2_PATH,
        help="e2-physics-auxiliary-v1 制品路径（含七字段与窗口键）",
    )
    parser.add_argument(
        "--tcp-path",
        type=Path,
        default=DEFAULT_TCP_PATH,
        help="tcp-sender-truth-v2 制品路径（逐窗口 8 发送者）",
    )
    parser.add_argument(
        "--which",
        choices=("d1", "d2", "v1", "v2", "v3", "both", "all"),
        default="both",
        help="运行范围：d1/d2/v1/v2/v3 单项；both 等价于 d1+d2（向后兼容）；"
        "all 等价于 d1+d2+v1+v2+v3（默认 both）",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        required=True,
        help="结果写出路径",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """命令行入口：装载两份制品、按 --which 运行 D1/D2/V1/V2/V3、写出结果 JSON。

    Args:
        argv: 命令行参数；为 None 时使用 sys.argv。

    Returns:
        退出码。0 表示探针流程本身成功执行（不代表 A' 或场景混淆结构性
        命题通过裁决，通过与否记录在输出 JSON 的 d1.passed / d2.verdict /
        v1.verdict / v2.verdict / v3.all_not_dominated_by_scene 等字段中）；
        非零表示数据装载或前置条件失败。
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_arg_parser().parse_args(argv)

    try:
        e2_frame = pd.read_parquet(args.e2_path)
        tcp_frame = pd.read_parquet(args.tcp_path)
        merged = compute_target_frame(e2_frame, tcp_frame)
        tcp_train_fit_frame = tcp_frame[tcp_frame["split_id"] == TRAIN_FIT_SPLIT_ID]
    except (TcpStateProbeError, OSError, ValueError) as exc:
        logger.error("数据装载失败：%s", exc)
        return 1

    result: dict[str, object] = {
        "e2_path": str(args.e2_path),
        "tcp_path": str(args.tcp_path),
        "n_windows": int(len(merged)),
        "random_seed": RANDOM_SEED,
    }

    which = args.which
    run_d1_flag = which in ("d1", "both", "all")
    run_d2_flag = which in ("d2", "both", "all")
    run_v1_flag = which in ("v1", "all")
    run_v2_flag = which in ("v2", "all")
    run_v3_flag = which in ("v3", "all")

    try:
        if run_d1_flag:
            result["d1"] = run_d1(merged, tcp_train_fit_frame)
            logger.info("D1 完成，passed=%s", result["d1"]["passed"])
        if run_d2_flag:
            result["d2"] = run_d2(merged)
            logger.info(
                "D2 完成，best_channel=%s best_r2=%.4f verdict=%s",
                result["d2"]["best_channel"],
                result["d2"]["best_r2"],
                result["d2"]["verdict"],
            )
        if run_v1_flag:
            result["v1"] = run_v1(merged)
            logger.info("V1 完成，verdict=%s", result["v1"]["verdict"])
        if run_v2_flag:
            result["v2"] = run_v2(merged)
            logger.info("V2 完成，verdict=%s", result["v2"]["verdict"])
        if run_v3_flag:
            result["v3"] = run_v3(tcp_train_fit_frame)
            logger.info(
                "V3 完成，all_not_dominated_by_scene=%s any_strong_form_confirmed=%s",
                result["v3"]["all_not_dominated_by_scene"],
                result["v3"]["any_strong_form_confirmed"],
            )
    except TcpStateProbeError as exc:
        logger.error("探针裁决前置条件不满足：%s", exc)
        return 1

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    logger.info("结果已写入 %s", args.output_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
