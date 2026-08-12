use std::collections::BTreeMap;

use serde::Serialize;

/// 仅引用宽表行号的历史索引记录。
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct HistoryRelationRow {
    pub horizon: u32,
    pub target_window_row_index: u64,
    pub next_window_row_index: Option<u64>,
    pub lag: u32,
    pub history_window_row_index: u64,
}

/// 从同一端点的已发布开发宽表行生成统一历史与下一窗关系。
pub fn build_history_relations(
    endpoint_rows: &BTreeMap<String, Vec<u64>>,
    horizons: &[usize],
) -> Vec<HistoryRelationRow> {
    let mut output = Vec::new();
    for rows in endpoint_rows.values() {
        for horizon in horizons {
            for (index, target_window_row_index) in rows.iter().copied().enumerate() {
                if index < *horizon {
                    continue;
                }
                let next_window_row_index = rows.get(index + 1).copied();
                for (offset, history_window_row_index) in
                    rows[index - horizon..index].iter().copied().enumerate()
                {
                    output.push(HistoryRelationRow {
                        horizon: u32::try_from(*horizon).unwrap_or(u32::MAX),
                        target_window_row_index,
                        next_window_row_index,
                        lag: u32::try_from(*horizon - offset).unwrap_or(u32::MAX),
                        history_window_row_index,
                    });
                }
            }
        }
    }
    output
}
