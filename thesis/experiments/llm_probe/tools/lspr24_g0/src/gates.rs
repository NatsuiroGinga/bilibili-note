//! G0-A 收据完整性、依赖与总状态归约。

use std::collections::{BTreeMap, BTreeSet};
use std::fs::File;
use std::io::{self, Read};

use serde::Serialize;
use sha2::{Digest, Sha256};

use crate::receipt::{
    GATE_CONFIG_SCHEMA_VERSION, GATE_RECEIPT_SCHEMA_VERSION, GateConfig, GateId, GateReceipt,
    GateStatus,
};
use crate::types::Sha256Digest;

const CORE_GATES: [GateId; 13] = [
    GateId::A01,
    GateId::A02,
    GateId::A03,
    GateId::A04,
    GateId::A05,
    GateId::A06,
    GateId::A07,
    GateId::A08,
    GateId::A09,
    GateId::A11,
    GateId::A12,
    GateId::A13,
    GateId::A14,
];

/// 冻结合同规定的 G0-A 总裁决。
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum OverallDecision {
    #[serde(rename = "NO_GO")]
    NoGo,
    #[serde(rename = "NOT_READY")]
    NotReady,
    #[serde(rename = "GO_TO_BASELINES_AND_EARLY_STOPPING")]
    GoToBaselinesAndEarlyStopping,
    #[serde(rename = "GO_TO_BASELINES_THIRD_ONLY")]
    GoToBaselinesThirdOnly,
}

/// A01 至 A14 的独立状态和总裁决。
#[derive(Debug, Clone)]
pub struct GateEvaluation {
    statuses: BTreeMap<GateId, GateStatus>,
    overall: OverallDecision,
}

impl GateEvaluation {
    /// 返回指定门禁状态；缺项固定视为 `NOT_READY`。
    #[must_use]
    pub fn status(&self, gate_id: GateId) -> GateStatus {
        self.statuses
            .get(&gate_id)
            .copied()
            .unwrap_or(GateStatus::NotReady)
    }

    /// 返回总裁决。
    #[must_use]
    pub const fn overall(&self) -> OverallDecision {
        self.overall
    }

    /// 返回完整有序状态表。
    #[must_use]
    pub fn statuses(&self) -> &BTreeMap<GateId, GateStatus> {
        &self.statuses
    }
}

/// 验证收据、合同、制品和固定依赖，并归约独立复算状态。
///
/// `independently_recomputed` 只能由读取原始制品的门禁谓词提供。收据内的
/// `checks` 汇总布尔值和生产者 `status` 均不进入该映射，也不参与裁决。
#[must_use]
pub fn evaluate_receipts(
    config: &GateConfig,
    receipts: &[GateReceipt],
    independently_recomputed: &BTreeMap<GateId, GateStatus>,
) -> GateEvaluation {
    let mut by_gate = BTreeMap::new();
    let mut duplicates = BTreeSet::new();
    for receipt in receipts {
        if by_gate.insert(receipt.gate_id(), receipt).is_some() {
            duplicates.insert(receipt.gate_id());
        }
    }

    let mut statuses = BTreeMap::new();
    for gate_id in GateId::ALL {
        let status = if duplicates.contains(&gate_id) {
            GateStatus::NotReady
        } else if let Some(receipt) = by_gate.get(&gate_id) {
            if receipt_is_ready(config, receipt, &by_gate, &statuses) {
                independently_recomputed
                    .get(&gate_id)
                    .copied()
                    .unwrap_or(GateStatus::NotReady)
            } else {
                GateStatus::NotReady
            }
        } else {
            GateStatus::NotReady
        };
        statuses.insert(gate_id, status);
    }

    let overall = reduce_overall(&statuses);
    GateEvaluation { statuses, overall }
}

fn receipt_is_ready(
    config: &GateConfig,
    receipt: &GateReceipt,
    receipts: &BTreeMap<GateId, &GateReceipt>,
    statuses: &BTreeMap<GateId, GateStatus>,
) -> bool {
    if config.schema_version() != GATE_CONFIG_SCHEMA_VERSION
        || receipt.schema_version() != GATE_RECEIPT_SCHEMA_VERSION
        || receipt.contract_version() != config.contract_version()
    {
        return false;
    }
    let Some(contract_sha256) = config.expected_contract_sha256() else {
        return false;
    };
    if receipt.contract_sha256() != contract_sha256
        || receipt.computed_sha256().ok() != Some(receipt.receipt_sha256())
        || !artifacts_match(receipt)
    {
        return false;
    }

    let required = receipt.gate_id().required_dependencies();
    if receipt.dependencies().len() != required.len() {
        return false;
    }
    for (declared, required_gate) in receipt.dependencies().iter().zip(required) {
        if declared.gate_id != *required_gate {
            return false;
        }
        let Some(dependency_receipt) = receipts.get(required_gate) else {
            return false;
        };
        if declared.receipt_sha256 != dependency_receipt.receipt_sha256()
            || statuses.get(required_gate) != Some(&GateStatus::Pass)
        {
            return false;
        }
    }
    true
}

fn artifacts_match(receipt: &GateReceipt) -> bool {
    receipt.input_artifacts().iter().all(|artifact| {
        file_sha256(artifact.path()).ok() == Some(artifact.sha256())
    })
}

fn file_sha256(path: &std::path::Path) -> Result<Sha256Digest, io::Error> {
    let mut file = File::open(path)?;
    let mut hasher = Sha256::new();
    let mut buffer = [0u8; 64 * 1024];
    loop {
        let read = file.read(&mut buffer)?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
    }
    Ok(hasher.finalize().into())
}

fn reduce_overall(statuses: &BTreeMap<GateId, GateStatus>) -> OverallDecision {
    if CORE_GATES
        .iter()
        .any(|gate_id| statuses.get(gate_id) == Some(&GateStatus::Fail))
    {
        return OverallDecision::NoGo;
    }
    if CORE_GATES
        .iter()
        .any(|gate_id| statuses.get(gate_id) != Some(&GateStatus::Pass))
    {
        return OverallDecision::NotReady;
    }
    if statuses.get(&GateId::A10) == Some(&GateStatus::Pass) {
        OverallDecision::GoToBaselinesAndEarlyStopping
    } else {
        OverallDecision::GoToBaselinesThirdOnly
    }
}
