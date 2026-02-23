# Registry Files Consolidation Script
# Generated: 2026-02-17
# Purpose: Move all registry files to C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY

param(
    [switch]$DryRun = $false,
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"
$TargetBase = "C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY"
$LogFile = Join-Path $TargetBase "consolidation_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage
    Add-Content -Path $LogFile -Value $logMessage
}

function Move-FileWithBackup {
    param(
        [string]$SourcePath,
        [string]$DestinationPath
    )
    
    if (-not (Test-Path $SourcePath)) {
        Write-Log "Source file not found: $SourcePath" "WARNING"
        return $false
    }
    
    $destDir = Split-Path $DestinationPath -Parent
    if (-not (Test-Path $destDir)) {
        if ($DryRun) {
            Write-Log "[DRY RUN] Would create directory: $destDir" "INFO"
        } else {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            Write-Log "Created directory: $destDir" "INFO"
        }
    }
    
    if (Test-Path $DestinationPath) {
        $backupPath = "$DestinationPath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        if ($DryRun) {
            Write-Log "[DRY RUN] Would backup existing: $DestinationPath -> $backupPath" "INFO"
        } else {
            Move-Item -Path $DestinationPath -Destination $backupPath -Force
            Write-Log "Backed up existing file: $backupPath" "INFO"
        }
    }
    
    if ($DryRun) {
        Write-Log "[DRY RUN] Would move: $SourcePath -> $DestinationPath" "INFO"
    } else {
        Move-Item -Path $SourcePath -Destination $DestinationPath -Force
        Write-Log "Moved: $SourcePath -> $DestinationPath" "SUCCESS"
    }
    
    return $true
}

Write-Log "========================================" "INFO"
Write-Log "Registry Files Consolidation Starting" "INFO"
Write-Log "Target Directory: $TargetBase" "INFO"
Write-Log "Dry Run Mode: $DryRun" "INFO"
Write-Log "========================================" "INFO"

# Create target subdirectories
$subdirs = @(
    "from_gov_reg_root",
    "from_gov_reg_subdirs",
    "from_all_ai",
    "backups_original",
    "scripts",
    "tests",
    "docs"
)

foreach ($subdir in $subdirs) {
    $path = Join-Path $TargetBase $subdir
    if (-not (Test-Path $path)) {
        if ($DryRun) {
            Write-Log "[DRY RUN] Would create subdirectory: $path" "INFO"
        } else {
            New-Item -ItemType Directory -Path $path -Force | Out-Null
            Write-Log "Created subdirectory: $path" "INFO"
        }
    }
}

# =============================================
# PHASE 1: Move Gov_Reg Root Files
# =============================================
Write-Log "PHASE 1: Moving Gov_Reg Root Files" "INFO"

$govRegRoot = "C:\Users\richg\Gov_Reg"
$govRegRootFiles = @(
    "01260207201000000138_governance_invariant_registry.json",
    "01999000042260124503_governance_registry_unified.json",
    "01999000042260124503_governance_registry_unified.json.backup",
    "01999000042260124503_governance_registry_unified.json.backup2",
    "01999000042260124503_governance_registry_unified.json.backup_20260215_090419",
    "01999000042260124503_governance_registry_unified.json.backup_20260216_073858",
    "01999000042260124012_governance_registry_schema.v3.json",
    "01260207201000000193_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml",
    "01260207201000000192_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml",
    "P_01260207201000000199_sync_registry_recursive.py",
    "registryfiles.txt",
    "01260207201000000186_REGISTRY_PLANNING_INTEGRATION_SPEC.md"
)

$destSubdir = Join-Path $TargetBase "from_gov_reg_root"
foreach ($file in $govRegRootFiles) {
    $sourcePath = Join-Path $govRegRoot $file
    $destPath = Join-Path $destSubdir $file
    Move-FileWithBackup -SourcePath $sourcePath -DestinationPath $destPath
}

# =============================================
# PHASE 2: Move Gov_Reg Subdirectory Files
# =============================================
Write-Log "PHASE 2: Moving Gov_Reg Subdirectory Files" "INFO"

# Define file mappings with relative paths
$govRegSubdirFiles = @(
    # newPhasePlanProcess
    @{Source = "newPhasePlanProcess\01260207201000001223_schemas\01260207201000000531_FILE_PURPOSE_REGISTRY.schema.v1.json"; Dest = "newPhasePlanProcess\schemas"},
    @{Source = "newPhasePlanProcess\01260207201000001222_Plans_Instructions\01260207201000000527_wobbly-purring-island_registry-integrated.plan.json"; Dest = "newPhasePlanProcess\plans"},
    @{Source = "newPhasePlanProcess\01260207201000001222_Plans_Instructions\01260207201000000520_Instructions_Deliver_Capabilities_Inventory_Purpose Registry.md"; Dest = "newPhasePlanProcess\plans"},
    @{Source = "newPhasePlanProcess\01260207201000001222_Plans_Instructions\01260207201000000519_Instructions_Deliver_Capabilities_Inventory_Purpose Registry.json"; Dest = "newPhasePlanProcess\plans"},
    @{Source = "newPhasePlanProcess\01260207201000001216_Docs\01260207201000000478_REGISTRY_PLANNING_INTEGRATION_SPEC.md"; Dest = "newPhasePlanProcess\docs"},
    @{Source = "newPhasePlanProcess\01260207201000001216_Docs\01260207201000000475_JSON_Schemas_CAPABILITIESFILE_INVENTORY_FILE_PURPOSE_REGISTRY.md"; Dest = "newPhasePlanProcess\docs"},
    @{Source = "newPhasePlanProcess\01260207201000001225_scripts\P_01260207233100000247_validate_artifact_registry.py"; Dest = "scripts\validation"},
    @{Source = "newPhasePlanProcess\01260207201000001217_mcp\01260207201000001219_tools\P_01260207201000000499_registry_snapshot_query.py"; Dest = "scripts\mcp_tools"},
    
    # docs/governance
    @{Source = "01260207201000001139_docs\01260207201000001140_governance\01999000042260125069_TEMPLATE_REGISTRY_USAGE.md"; Dest = "docs\templates"},
    @{Source = "01260207201000001139_docs\01260207201000001140_governance\01999000042260125068_TEMPLATE_REGISTRY_RUNBOOK.md"; Dest = "docs\templates"},
    @{Source = "01260207201000001139_docs\01260207201000001140_governance\01999000042260125067_TEMPLATE_REGISTRY_README.md"; Dest = "docs\templates"},
    
    # OLD_MD_DOCUMENTS_FOR_REVIEW (move to docs/archive)
    @{Source = "01260207201000001231_OLD_MD_DOCUMENTS_FOR_REVIEW\01260207201000001240_PRMNT DOCS\01260207201000000753_DOC_ID_REGISTRY_CLI_REVIEW.md"; Dest = "docs\archive"},
    @{Source = "01260207201000001231_OLD_MD_DOCUMENTS_FOR_REVIEW\01260207201000001237_EVERYTHING ELES_878\01260207201000000630_REGISTRY.md"; Dest = "docs\archive"},
    @{Source = "01260207201000001231_OLD_MD_DOCUMENTS_FOR_REVIEW\Governance Registry Design.docx"; Dest = "docs\archive"},
    
    # FILE WATCHER
    @{Source = "01260207201000001158_FILE WATCHER\01260207233100000432_File Watch System Capability Registry.yml"; Dest = "config\file_watcher"},
    @{Source = "01260207201000001158_FILE WATCHER\01260207201000000382_Registry update events (recompute_on_scan).md"; Dest = "docs\file_watcher"},
    
    # monitoring
    @{Source = "01260207201000001228_monitoring\01260207201000001230_dashboards\01260207201000000540_registry_operations.json"; Dest = "config\monitoring"},
    
    # PATH_FILES
    @{Source = "01260207201000001242_PATH_FILES\P_01260207233100000026_path_registry.py"; Dest = "scripts\path_registry"},
    @{Source = "01260207201000001242_PATH_FILES\01260207201000001248_scripts\P_01999000042260126009_path_registry_watcher.py"; Dest = "scripts\path_registry"},
    
    # EVIDENCE_BUNDLE (keep as-is, just document location)
    @{Source = "EVIDENCE_BUNDLE\diffs\registry.patch.rfc6902.json"; Dest = "evidence\diffs"},
    @{Source = "EVIDENCE_BUNDLE\reports\registry_patch_report.md"; Dest = "evidence\reports"},
    
    # config
    @{Source = "01260207201000001137_config\P_01260207233100000003_registry_paths.py"; Dest = "config"},
    
    # govreg_core
    @{Source = "01260207201000001173_govreg_core\P_01999000042260125108_registry_fs_reconciler.py"; Dest = "scripts\govreg_core"},
    @{Source = "01260207201000001173_govreg_core\P_01260207233100000072_registry_schema_extension.py"; Dest = "scripts\govreg_core"},
    @{Source = "01260207201000001173_govreg_core\P_01260207233100000018_registry_schema_v3.py"; Dest = "scripts\govreg_core"},
    @{Source = "01260207201000001173_govreg_core\01260207201000001174_geu_reconciliation\P_01260207233100000156_registry_loader.py"; Dest = "scripts\govreg_core\geu_reconciliation"},
    
    # src directory
    @{Source = "01260207201000001289_src\01260207201000001297_registry_writer\P_01260207233100000335_registry_writer_service_v2.py"; Dest = "scripts\registry_writer"},
    @{Source = "01260207201000001289_src\01260207201000001296_registry_transition\P_01260207233100000325_registry_writer.py"; Dest = "scripts\registry_transition"},
    @{Source = "01260207201000001289_src\01260207201000001290_capability_mapping\P_01260207201000000985_P_01260207233100000YYY_registry_promoter.py"; Dest = "scripts\capability_mapping"},
    @{Source = "01260207201000001289_src\01260207201000001290_capability_mapping\P_01260207201000000984_P_01260207233100000YYY_purpose_registry_builder.py"; Dest = "scripts\capability_mapping"},
    
    # scripts directory
    @{Source = "01260207201000001276_scripts\P_01999000042260125110_populate_registry_dir_ids_enhanced.py"; Dest = "scripts\utilities"},
    @{Source = "01260207201000001276_scripts\P_01999000042260125104_update_registry_paths.py"; Dest = "scripts\utilities"},
    @{Source = "01260207201000001276_scripts\P_01999000042260125102_populate_registry_dir_ids.py"; Dest = "scripts\utilities"},
    @{Source = "01260207201000001276_scripts\P_01260207233100000029_align_registry_dictionary.py"; Dest = "scripts\utilities"},
    @{Source = "01260207201000001276_scripts\01260207201000001285_utilities\P_01260207233100000316_01999000042260125065_registry_store.py"; Dest = "scripts\utilities"},
    @{Source = "01260207201000001276_scripts\01260207201000001285_utilities\P_01260207233100000314_01999000042260125063_2026012120420011_registry_cli.py"; Dest = "scripts\utilities"},
    @{Source = "01260207201000001276_scripts\01260207201000001285_utilities\P_01260207233100000313_01999000042260125062_2026012120420010_normalize_registry.py"; Dest = "scripts\utilities"},
    @{Source = "01260207201000001276_scripts\01260207201000001284_phase_b\P_01260207233100000309_01999000042260125057_2026012201111007_create_file_registry.py"; Dest = "scripts\phase_b"},
    @{Source = "01260207201000001276_scripts\01260207201000001284_phase_b\P_01260207233100000308_01999000042260125056_2026012201111005_generate_module_registry.py"; Dest = "scripts\phase_b"},
    @{Source = "01260207201000001276_scripts\01260207201000001282_migration\P_01260207233100000289_analyze_registry.py"; Dest = "scripts\migration"},
    @{Source = "01260207201000001276_scripts\01260207201000001278_deployment\P_01260207201000000886_backup_registry.py"; Dest = "scripts\deployment"},
    
    # tests
    @{Source = "01260207201000001305_tests\P_01260207233100000057_test_registry_writer.py"; Dest = "tests"},
    @{Source = "01260207201000001305_tests\P_01260207233100000056_test_registry_schema_v3.py"; Dest = "tests"},
    @{Source = "01260207201000001305_tests\01260207201000001308_integration\P_01260207201000001008_test_registry_operations.py"; Dest = "tests\integration"},
    
    # backups
    @{Source = "01260207201000001133_backups\01260207201000001134_doc_id_migration\01260207201000001135_REGISTRY\01999000042260124503_governance_registry_unified.json"; Dest = "backups_original\doc_id_migration"}
)

$destSubdirBase = Join-Path $TargetBase "from_gov_reg_subdirs"
foreach ($fileMapping in $govRegSubdirFiles) {
    $sourcePath = Join-Path $govRegRoot $fileMapping.Source
    $destDir = Join-Path $destSubdirBase $fileMapping.Dest
    $fileName = Split-Path $fileMapping.Source -Leaf
    $destPath = Join-Path $destDir $fileName
    
    Move-FileWithBackup -SourcePath $sourcePath -DestinationPath $destPath
}

# =============================================
# PHASE 3: Move ALL_AI Files to Single Folder
# =============================================
Write-Log "PHASE 3: Moving ALL_AI Registry Files" "INFO"

$allAIBase = "C:\Users\richg\ALL_AI"
$allAIDestBase = Join-Path $TargetBase "from_all_ai"

# Create subdirectory structure for ALL_AI files
$allAISubdirs = @(
    "data",
    "governance",
    "workflows",
    "runtime",
    "reference",
    "process_for_all",
    "mini_pipe",
    "modules",
    "scripts",
    "migrations",
    "uti_tools",
    "config",
    "other"
)

foreach ($subdir in $allAISubdirs) {
    $path = Join-Path $allAIDestBase $subdir
    if (-not (Test-Path $path)) {
        if ($DryRun) {
            Write-Log "[DRY RUN] Would create subdirectory: $path" "INFO"
        } else {
            New-Item -ItemType Directory -Path $path -Force | Out-Null
        }
    }
}

# Define ALL_AI file mappings
$allAIFiles = @(
    # Root-level
    @{Source = "Governance Registry CLI Application.md"; Dest = "other"},
    
    # Data
    @{Source = "data\DOC-CONFIG-ID-REGISTRY-435__id_registry.json"; Dest = "data"},
    @{Source = "data\schemas\numeric_prefix_registry.schema.json"; Dest = "data\schemas"},
    @{Source = "data\schemas\DOC-REGISTRY-SCHEMA-ID-001__SCHEMA_REGISTRY.yaml"; Dest = "data\schemas"},
    @{Source = "data\schemas\DOC-REGISTRY-PAYLOAD-SCHEMA-001__PAYLOAD_SCHEMA_REGISTRY.yaml"; Dest = "data\schemas"},
    @{Source = "data\schemas\DOC-REGISTRY-MSG-TYPE-001__MESSAGE_TYPE_REGISTRY.yaml"; Dest = "data\schemas"},
    
    # GOVERNANCE - SSOT
    @{Source = "GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CONFIG-ID-REGISTRY-847__id_registry.json"; Dest = "governance\ssot\tools"},
    @{Source = "GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py"; Dest = "governance\ssot\tools"},
    @{Source = "GOVERNANCE\ssot\SSOT_System\SSOT_SYS_schemas\DOC-CONFIG-ID-REGISTRY-SCHEMA-842__id_registry.schema.json"; Dest = "governance\ssot\schemas"},
    @{Source = "GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tests\unit\DOC-TEST-UNIT-TEST-ID-REGISTRY-641__test_id_registry.py"; Dest = "governance\ssot\tests"},
    
    # GOVERNANCE - Other
    @{Source = "GOVERNANCE\lifecycle\DOC-CONFIG-UNIVERSAL-REGISTRY-ENTRY-SCHEMA-495__universal_registry_entry.schema.json"; Dest = "governance\lifecycle"},
    @{Source = "GOVERNANCE\rules\REGISTRY_CONFIG.yaml"; Dest = "governance\rules"},
    @{Source = "GOVERNANCE\rules\DOC-REGISTRY-RULE-ID-001__RULE_REGISTRY.yaml"; Dest = "governance\rules"},
    @{Source = "GOVERNANCE\policies\REGISTRY_CONFIG.yaml"; Dest = "governance\policies"},
    @{Source = "GOVERNANCE\policies\DOC-REGISTRY-POLICY-ID-001__POLICY_REGISTRY.yaml"; Dest = "governance\policies"},
    @{Source = "GOVERNANCE\precedents\REGISTRY_CONFIG.yaml"; Dest = "governance\precedents"},
    @{Source = "GOVERNANCE\precedents\DOC-REGISTRY-PRECEDENT-ID-001__PRECEDENT_REGISTRY.yaml"; Dest = "governance\precedents"},
    @{Source = "GOVERNANCE\gates\REGISTRY_CONFIG.yaml"; Dest = "governance\gates"},
    @{Source = "GOVERNANCE\gates\DOC-REGISTRY-GATE-ID-001__GATE_REGISTRY.yaml"; Dest = "governance\gates"},
    
    # WORKFLOWS
    @{Source = "WORKFLOWS\workstreams\DOC-REGISTRY-WORKSTREAM-ID-001__WORKSTREAM_REGISTRY.yaml"; Dest = "workflows"},
    @{Source = "WORKFLOWS\contracts\DOC-REGISTRY-CONTRACT-ID-001__CONTRACT_REGISTRY.yaml"; Dest = "workflows"},
    @{Source = "WORKFLOWS\chains\DOC-REGISTRY-CHAIN-ID-001__CHAIN_REGISTRY.yaml"; Dest = "workflows"},
    
    # RUNTIME - Top level registries
    @{Source = "RUNTIME\traces\DOC-REGISTRY-TRACE-ID-001__TRACE_REGISTRY.yaml"; Dest = "runtime"},
    @{Source = "RUNTIME\symbols\DOC-REGISTRY-SYMBOL-ID-001__SYMBOL_REGISTRY.yaml"; Dest = "runtime"},
    @{Source = "RUNTIME\runs\DOC-REGISTRY-RUN-ID-001__RUN_REGISTRY.yaml"; Dest = "runtime"},
    @{Source = "RUNTIME\process_steps\DOC-REGISTRY-STEP-ID-001__STEP_REGISTRY.yaml"; Dest = "runtime"},
    @{Source = "RUNTIME\pipelines\DOC-REGISTRY-PIPELINE-ID-001__PIPELINE_REGISTRY.yaml"; Dest = "runtime"},
    @{Source = "RUNTIME\outcomes\DOC-REGISTRY-OUTCOME-ID-001__OUTCOME_REGISTRY.yaml"; Dest = "runtime"},
    @{Source = "RUNTIME\metrics\DOC-REGISTRY-METRIC-ID-001__METRIC_REGISTRY.yaml"; Dest = "runtime"},
    @{Source = "RUNTIME\hooks\DOC-REGISTRY-HOOK-ID-001__HOOK_REGISTRY.yaml"; Dest = "runtime"},
    @{Source = "RUNTIME\graph\DOC-REGISTRY-GRAPH-EDGE-ID-001__EDGE_REGISTRY.yaml"; Dest = "runtime"},
    @{Source = "RUNTIME\events\DOC-REGISTRY-EVENT-ID-001__EVENT_REGISTRY.yaml"; Dest = "runtime"},
    @{Source = "RUNTIME\evaluations\DOC-REGISTRY-EVALUATION-ID-001__EVAL_REGISTRY.yaml"; Dest = "runtime"},
    @{Source = "RUNTIME\errors\DOC-REGISTRY-ERROR-CODE-001__ERROR_REGISTRY.yaml"; Dest = "runtime"},
    @{Source = "RUNTIME\deployments\DOC-REGISTRY-DEPLOYMENT-ID-001__DEPLOY_REGISTRY.yaml"; Dest = "runtime"},
    @{Source = "RUNTIME\definitions\DOC-REGISTRY-DEFINITION-ID-001__DEF_REGISTRY.yaml"; Dest = "runtime"},
    @{Source = "RUNTIME\correlation\DOC-REGISTRY-CORRELATION-ID-001__CORR_REGISTRY.yaml"; Dest = "runtime"},
    @{Source = "RUNTIME\callsites\DOC-REGISTRY-CALLSITE-ID-001__CALLSITE_REGISTRY.yaml"; Dest = "runtime"},
    @{Source = "RUNTIME\alerts\DOC-REGISTRY-ALERT-ID-001__ALERT_REGISTRY.yaml"; Dest = "runtime"},
    
    # RUNTIME - path_registry
    @{Source = "RUNTIME\path_registry\SUB_PATH_REGISTRY\DOC-REGISTRY-PATH-KEY-001__path_key_registry.yaml"; Dest = "runtime\path_registry"},
    @{Source = "RUNTIME\path_registry\SUB_PATH_REGISTRY\DOC-CONFIG-DIR-MANIFEST-RUNTIME-PATH-REGISTRY-SUB-PATH-REGISTRY-1031__DIR_MANIFEST.yaml"; Dest = "runtime\path_registry"},
    
    # RUNTIME - doc_id (selection of key files)
    @{Source = "RUNTIME\doc_id\SUB_DOC_ID\DOC-REGISTRY-ID-TYPES-001__ID_TYPE_REGISTRY.yaml"; Dest = "runtime\doc_id"},
    @{Source = "RUNTIME\doc_id\SUB_DOC_ID\DOC-VALIDATOR-ID-TYPE-REGISTRY-001__validate_id_type_registry.py"; Dest = "runtime\doc_id"},
    @{Source = "RUNTIME\doc_id\SUB_DOC_ID\common\DOC-CORE-COMMON-REGISTRY-1171__registry.py"; Dest = "runtime\doc_id"},
    @{Source = "RUNTIME\doc_id\SUB_DOC_ID\1_CORE_OPERATIONS\DOC-CORE-1-CORE-OPERATIONS-REGISTRY-LOCK-1155__registry_lock.py"; Dest = "runtime\doc_id\core"},
    @{Source = "RUNTIME\doc_id\SUB_DOC_ID\5_REGISTRY_DATA\DOC-SCRIPT-1014__sync_doc_id_registry.py"; Dest = "runtime\doc_id"},
    
    # PROCESS_FOR_ALL
    @{Source = "PROCESS_FOR_ALL\CLP_PROCESS\schemas\debug_prompt_registry.schema.json"; Dest = "process_for_all"},
    @{Source = "PROCESS_FOR_ALL\CLP_PROCESS\extracted_files\DBG-REGISTRY.yaml"; Dest = "process_for_all"},
    @{Source = "PROCESS_FOR_ALL\CLP_PROCESS\registry_reference.md"; Dest = "process_for_all"},
    @{Source = "PROCESS_FOR_ALL\CLP_PROCESS\src\orchestrator\plugin_registry.py"; Dest = "process_for_all"},
    
    # MINI_PIPE
    @{Source = "MINI_PIPE\src\acms\path_registry.py"; Dest = "mini_pipe"},
    @{Source = "MINI_PIPE\src\acms\gap_registry.py"; Dest = "mini_pipe"},
    @{Source = "MINI_PIPE\tests\test_path_registry.py"; Dest = "mini_pipe\tests"},
    @{Source = "MINI_PIPE\tests\unit\test_gap_registry.py"; Dest = "mini_pipe\tests"},
    
    # modules
    @{Source = "modules\path_abstraction\DOC-CORE-PATH-ABSTRACTION-PATH-REGISTRY-192__path_registry.py"; Dest = "modules"},
    @{Source = "modules\path_abstraction\DOC-SCRIPT-1320__path_registry.py"; Dest = "modules"},
    
    # scripts
    @{Source = "scripts\validators\DOC-VALIDATOR-REGISTRY-LOCKING-001__validate_registry_locking.py"; Dest = "scripts\validators"},
    @{Source = "scripts\migration\DOC-SCRIPT-MIGRATE-TO-PATHREGISTRY-001__generate_migration_plan.py"; Dest = "scripts\migration"},
    @{Source = "scripts\generators\DOC-SCRIPT-0991__generate_id_registry.py"; Dest = "scripts\generators"},
    
    # MIGRATIONS
    @{Source = "MIGRATIONS\DIR_ID_PATH_DISAMBIGUATION\scripts\DOC-SCRIPT-1289__validate_path_registry.py"; Dest = "migrations"},
    
    # UTI_TOOLS
    @{Source = "UTI_TOOLS\DOC-CORE-UTI-TOOLS-VALIDATE-REGISTRY-823__validate_registry.py"; Dest = "uti_tools"},
    @{Source = "UTI_TOOLS\DOC-SCRIPT-UTI-VALIDATE-CROSS-SYNC-001__validate_cross_registry_sync.py"; Dest = "uti_tools"},
    @{Source = "UTI_TOOLS\coverage_analyzer\src\coverage_analyzer\DOC-CORE-COVERAGE-ANALYZER-REGISTRY-465__registry.py"; Dest = "uti_tools"},
    
    # config
    @{Source = "config\DOC-REGISTRY-CONFIG-ID-001__CONFIG_REGISTRY.yaml"; Dest = "config"},
    @{Source = "config\environments\DOC-REGISTRY-ENVIRONMENT-ID-001__ENV_REGISTRY.yaml"; Dest = "config"},
    
    # Other top-level
    @{Source = "glossary\DOC-REGISTRY-TERM-ID-001__GLOSSARY_REGISTRY.yaml"; Dest = "other"},
    @{Source = "benchmarks\DOC-REGISTRY-BENCHMARK-ID-001__BENCHMARK_REGISTRY.yaml"; Dest = "other"},
    @{Source = "AI_CLI_PROVENANCE_SOLUTION\tests\fixtures\DOC-TEST-FIXTURE-SAMPLE-REGISTRY-001__sample_registry.yaml"; Dest = "other"}
)

foreach ($fileMapping in $allAIFiles) {
    $sourcePath = Join-Path $allAIBase $fileMapping.Source
    $destDir = Join-Path $allAIDestBase $fileMapping.Dest
    $fileName = Split-Path $fileMapping.Source -Leaf
    $destPath = Join-Path $destDir $fileName
    
    Move-FileWithBackup -SourcePath $sourcePath -DestinationPath $destPath
}

# =============================================
# Final Summary
# =============================================
Write-Log "========================================" "INFO"
Write-Log "Registry Files Consolidation Complete" "INFO"
Write-Log "========================================" "INFO"
Write-Log "Review log file: $LogFile" "INFO"

if ($DryRun) {
    Write-Log "" "INFO"
    Write-Log "DRY RUN COMPLETED - No files were actually moved" "INFO"
    Write-Log "Review the log above and run without -DryRun to execute" "INFO"
}
