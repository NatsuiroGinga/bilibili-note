//! 规则表展开、源列类型回填与禁入断言。

use std::collections::BTreeSet;

use crate::schema_audit::SchemaAudit;

use super::rules::rule_entries;
use super::{
    AVAILABILITY_TIME_WINDOW_END, FORBIDDEN_SOURCE_COLUMNS, FieldManifestEntry, FieldManifestError,
    WINDOW_AGG_FORMULA_VERSION,
};

const OUTPUT_NAME_PREFIX: &str = "win_";

/// 把精确源列名规范化为输出列名的下划线短名。
///
/// 规则：全部小写，任意非字母数字连续段折叠为单个 `_`，并去掉首尾 `_`。
#[must_use]
pub fn output_column_slug(column: &str) -> String {
    let mut slug = String::with_capacity(column.len());
    let mut pending_separator = false;
    for character in column.chars() {
        if character.is_ascii_alphanumeric() {
            if pending_separator && !slug.is_empty() {
                slug.push('_');
            }
            pending_separator = false;
            slug.push(character.to_ascii_lowercase());
        } else {
            pending_separator = true;
        }
    }
    slug
}

/// 按聚合规则表展开完整字段清单，源列类型全部取自模式审计。
///
/// # Errors
///
/// 规则表引用了审计清单之外的源列、命中禁入黑名单，或展开结果不满足唯一性与
/// 前缀约束时返回错误。
pub fn build_field_manifest(
    audit: &SchemaAudit,
) -> Result<Vec<FieldManifestEntry>, FieldManifestError> {
    let rules = rule_entries();
    let mut entries = Vec::with_capacity(rules.len());
    for rule in rules {
        let mut source_columns = Vec::with_capacity(rule.source_columns.len());
        let mut source_schema_types = Vec::with_capacity(rule.source_columns.len());
        for column in rule.source_columns {
            if FORBIDDEN_SOURCE_COLUMNS.contains(&column) {
                return Err(FieldManifestError::ForbiddenSourceColumn {
                    output_name: rule.output_name.clone(),
                    column: column.to_owned(),
                });
            }
            let arrow_type = audit.arrow_type_of(column).ok_or_else(|| {
                FieldManifestError::UnknownSourceColumn {
                    output_name: rule.output_name.clone(),
                    column: column.to_owned(),
                }
            })?;
            source_columns.push(column.to_owned());
            source_schema_types.push(arrow_type.to_owned());
        }

        entries.push(FieldManifestEntry {
            output_name: rule.output_name,
            semantic_group: rule.semantic_group,
            source_columns,
            source_schema_types,
            availability_time: AVAILABILITY_TIME_WINDOW_END,
            aggregation_operator: rule.aggregation_operator,
            formula_version: WINDOW_AGG_FORMULA_VERSION,
            unit: rule.unit.to_owned(),
            direction_semantics: rule.direction_semantics,
            missing_rule: rule.missing_rule,
            transform: rule.transform,
            train_fit_parameter_hash: None,
            generation_target: rule.generation_target,
            allowed_models: vec!["ALL".to_owned()],
        });
    }

    validate_field_manifest(&entries, audit)?;
    Ok(entries)
}

/// 独立校验字段清单：输出列唯一、源列合法且类型与模式审计一致。
///
/// # Errors
///
/// 清单为空、输出列重名或前缀非法、源列含通配符、命中禁入黑名单、不在审计清单
/// 内或类型不一致时返回错误。
pub fn validate_field_manifest(
    entries: &[FieldManifestEntry],
    audit: &SchemaAudit,
) -> Result<(), FieldManifestError> {
    if entries.is_empty() {
        return Err(FieldManifestError::EmptyManifest);
    }

    let mut seen: BTreeSet<&str> = BTreeSet::new();
    for entry in entries {
        if !entry.output_name.starts_with(OUTPUT_NAME_PREFIX) {
            return Err(FieldManifestError::InvalidOutputName {
                output_name: entry.output_name.clone(),
            });
        }
        if !seen.insert(entry.output_name.as_str()) {
            return Err(FieldManifestError::DuplicateOutputName {
                output_name: entry.output_name.clone(),
            });
        }
        if entry.source_columns.len() != entry.source_schema_types.len() {
            return Err(FieldManifestError::SourceArityMismatch {
                output_name: entry.output_name.clone(),
                columns: entry.source_columns.len(),
                types: entry.source_schema_types.len(),
            });
        }

        for (column, declared) in entry
            .source_columns
            .iter()
            .zip(entry.source_schema_types.iter())
        {
            if column.contains('*') {
                return Err(FieldManifestError::WildcardSourceColumn {
                    output_name: entry.output_name.clone(),
                    column: column.clone(),
                });
            }
            if FORBIDDEN_SOURCE_COLUMNS.contains(&column.as_str()) {
                return Err(FieldManifestError::ForbiddenSourceColumn {
                    output_name: entry.output_name.clone(),
                    column: column.clone(),
                });
            }
            let arrow_type = audit.arrow_type_of(column).ok_or_else(|| {
                FieldManifestError::UnknownSourceColumn {
                    output_name: entry.output_name.clone(),
                    column: column.clone(),
                }
            })?;
            if arrow_type != declared {
                return Err(FieldManifestError::SourceTypeMismatch {
                    output_name: entry.output_name.clone(),
                    column: column.clone(),
                    expected: arrow_type.to_owned(),
                    actual: declared.clone(),
                });
            }
        }
    }

    Ok(())
}
