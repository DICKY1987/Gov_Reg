---
status: draft
doc_type: guide
module_refs: []
script_refs: []
doc_id: DOC-GUIDE-DOC-AI-DEV-HYGIENE-GUIDELINES-801
---

# AI Development Hygiene - Quick Reference Guidelines

**Purpose:** Maintain context clarity for AI-assisted development
**Audience:** Developers working with AI coding assistants (Aider, Codex, Claude)
**Version:** 1.0 | **Date:** 2025-11-20

---

## 🎯 Core Principles

### 1. **Separation of Concerns**
```
ACTIVE CODE ≠ REFERENCE DOCS ≠ ARCHIVE
```
Never mix production code with legacy examples or external references in the same directory.

### 2. **Explicit Status Tagging**
Every file must declare its role:
- **ACTIVE** - In production use
- **REFERENCE** - Consulted but not executed
- **DRAFT** - Work in progress
- **ARCHIVED** - Historical record only
- **EXTERNAL** - Copied from external source

### 3. **Context Boundaries**
AI tools should only see files relevant to current task. Use `.aiignore`, `.aiderignore`, or directory annotations.

---

## 📁 Directory Organization Rules

### Rule 1: 4-Layer Maximum Depth
```
✅ GOOD:
/core/engine/orchestrator/state_machine.py

❌ BAD:
/pipeline/src/modules/components/subcomponents/utils/helpers/state.py
```

**Why:** Deep nesting confuses AI context and makes navigation hard.

---

### Rule 2: Purpose-Named Directories
```
✅ GOOD:
/specs          # Canonical specifications
/docs           # Living documentation
/reference      # Stable references
/_archive       # Historical artifacts

❌ BAD:
/stuff
/misc
/temp
/old_versions
```

**Why:** Clear names help AI tools understand relevance.

---

### Rule 3: Isolate Archives
```
✅ GOOD:
/_archive/exploration/early_draft.md
[File excluded from AI indexing]

❌ BAD:
/early_draft_OLD_DO_NOT_USE.md
[AI still sees and might use it]
```

**Why:** Prefix `_` signals exclusion. Explicit exclusion patterns prevent confusion.

---

## 📝 File Naming Standards

### Convention: `[CATEGORY]_[SUBJECT]_[VERSION].[ext]`

**Categories:**
| Prefix | Purpose | Example |
|--------|---------|---------|
| `SPEC_` | Specifications | `SPEC_ORCHESTRATOR_V1.md` |
| `GUIDE_` | How-to guides | `GUIDE_PROMPT_ENGINEERING.md` |
| `REF_` | Reference docs | `REF_ANTHROPIC_PROMPTS.md` |
| `IMPL_` | Implementation | `IMPL_SUMMARY_M1.md` |
| `ARCH_` | Architecture | `ARCH_HEXAGONAL_PATTERN.md` |
| `SESSION_` | Session reports | `SESSION_REPORT_2025-11-19.md` |

**Examples:**
```
✅ GOOD:
SPEC_AGENT_OPERATIONS_V1.0.0.md
GUIDE_WORKSTREAM_AUTHORING.md
REF_PROMPT_PATTERNS_2025-01.md

❌ BAD:
my spec.md
guide (1).md
Reference - Copy.md
```

---

## 🏷️ File Header Standards

### Required Frontmatter (Markdown)

```markdown
---
status: ACTIVE | REFERENCE | DRAFT | ARCHIVED | EXTERNAL
ai_context_priority: P0 | P1 | P2 | P3 | P4
last_reviewed: YYYY-MM-DD
superseded_by: [path/to/newer/version.md]  # If applicable
source: INTERNAL | EXTERNAL:[Origin]
---

# Document Title

**Purpose:** One-line purpose statement

**Last Updated:** YYYY-MM-DD
```

### Example:

```markdown
---
status: ACTIVE
ai_context_priority: P0
last_reviewed: 2025-11-20
superseded_by: null
source: INTERNAL
---

# Agent Operations Specification v1.0.0

**Purpose:** Canonical contract for AI agent orchestration behavior

**Last Updated:** 2025-11-19
```

---

## 🚦 Context Priority Levels

| Priority | When to Use | AI Indexing | Lifecycle |
|----------|-------------|-------------|-----------|
| **P0** | Active specs, contracts | Always indexed | Review monthly |
| **P1** | Production code | Always indexed | Review quarterly |
| **P2** | Current guides | Index on request | Review quarterly |
| **P3** | Reference material | Explicit only | Review annually |
| **P4** | Archive/legacy | Never indexed | Delete after 2 years if unused |

**Implementation:**

Add to directory `.aicontext` file:
```yaml
# .aicontext
directory_purpose: "Core production orchestration engine"
ai_indexing: PRIORITY  # PRIORITY | STANDARD | LOW | EXCLUDE
context_scope: ACTIVE_CODE
```

---

## 🔒 Pre-Commit Checklist

Before committing new files to `/core`, `/specs`, or `/docs`:

### ✅ File Quality Gates

- [ ] **Purpose Clear:** First paragraph states purpose explicitly
- [ ] **Status Tagged:** Frontmatter includes status and priority
- [ ] **No Duplicates:** Searched existing files for similar content
- [ ] **Naming Convention:** Follows `CATEGORY_SUBJECT_VERSION` pattern
- [ ] **Context Appropriate:** File placed in correct directory for its purpose
- [ ] **Links Valid:** All internal links resolve correctly
- [ ] **AI Safe:** No legacy/outdated content that might confuse AI

### ✅ Code Quality Gates (Python/Scripts)

- [ ] **Imports Clean:** No unused imports
- [ ] **Docstrings Present:** All public functions documented
- [ ] **Type Hints:** Function signatures include types
- [ ] **Tests Exist:** Unit tests written and passing
- [ ] **No Hardcoded Paths:** Use path abstraction utilities

---

## 🗑️ Deletion Policy

### When to Archive (Not Delete)

Archive to `_archive/` if:
- File contains historical context that might be referenced
- Contains unique ideas/patterns not captured elsewhere
- Part of audit trail (session reports, decisions)

**Process:**
```powershell
# Move to archive with context
Move-Item "old_file.md" "_archive/exploration/"
# Add entry to _archive/README.md explaining why archived
```

### When to Delete Permanently

Delete if:
- Duplicate of existing active file (SHA256 hash match)
- Temporary file (e.g., `temp_notes.txt`, `draft_DELETEME.md`)
- External copy now available via URL/citation
- Zero references for >2 years (for archived files)

**Process:**
```powershell
# Log before delete
Get-FileHash "file_to_delete.md" | Out-File "DELETION_LOG.txt" -Append
# Delete
Remove-Item "file_to_delete.md"
```

---

## 📚 Reference Material Handling

### External References

**Tag clearly:**
```markdown
---
status: EXTERNAL
source: EXTERNAL:Anthropic:2025-01
ai_context_priority: P3
---

# Anthropic Prompt Engineering Guide (External Reference)

> **Source:** [Anthropic Documentation](https://docs.anthropic.com/...)
> **Retrieved:** 2025-01-15
> **License:** [Check source]

[Content...]
```

**Storage:**
```
/reference/external/
  ├── anthropic_prompt_guide_2025-01.md
  ├── openai_best_practices_2025-01.md
  └── _EXTERNAL_SOURCES.md  # Index of all external references
```

---

## 🔄 Quarterly Maintenance Routine

### Every 3 Months

**Week 1: Inventory**
```powershell
# Run health check
.\scripts\directory_health_check.ps1
```

**Week 2: Review**
- [ ] Check for new duplicates
- [ ] Update outdated documentation
- [ ] Review `P2` files - promote to `P1` or demote to `P3`
- [ ] Archive files with no edits in >6 months

**Week 3: Clean**
- [ ] Delete confirmed duplicates
- [ ] Update broken links
- [ ] Consolidate similar reference materials

**Week 4: Document**
- [ ] Update README with any structural changes
- [ ] Regenerate architecture diagrams
- [ ] Update this guideline if new patterns emerge

---

## 🤖 AI Tool-Specific Practices

### For Aider

**Context Control:**
```bash
# Only index specific directories
aider --read core/engine/orchestrator/*.py --read specs/contracts/*.md

# Exclude archives
# Create .aiderignore:
_archive/
reference/external/
*.txt
```

**Best Practice:**
- Start sessions with explicit file scope
- Use `--read` for reference-only files
- Use `--yes` only after validating AI's understanding

---

### For Codex CLI

**Context Control:**
```bash
# Codex respects .gitignore
# Add to .gitignore:
_archive/
reference/external/
```

**Best Practice:**
- Provide explicit task descriptions
- Reference specific files in prompts: "Edit `core/engine/orchestrator/core.py`"
- Use workspace mode for multi-file changes

---

### For Claude Code

**Context Control:**
```yaml
# .claude_context.yaml
exclude_patterns:
  - "_archive/**"
  - "reference/external/**"
  - "**/*.txt"

priority_paths:
  - "core/**/*.py"
  - "specs/contracts/*.md"
```

**Best Practice:**
- Use project-level context files
- Explicitly list high-priority files in prompts
- Review suggested changes before applying

---

## 🎓 Training: Onboarding New Team Members

### Day 1: Structure Walkthrough

1. **Clone repository**
2. **Read:** `README.md` → `ARCHITECTURE.md` → This file
3. **Explore:**
   ```powershell
   tree /F /A core | more
   tree /F /A specs | more
   tree /F /A docs | more
   ```
4. **Review:** Active specs in `/specs/contracts`

### Week 1: First Contribution

1. **Create feature branch**
2. **Add new file** following naming convention
3. **Include frontmatter** with status and priority
4. **Run pre-commit checks:**
   ```powershell
   .\scripts\validate_new_file.ps1 -FilePath "my_new_file.md"
   ```
5. **Submit PR** with clear description

---

## 📊 Success Metrics

### Individual File Quality

✅ **PASS Criteria:**
- Has clear frontmatter with status and priority
- Filename follows convention
- Placed in appropriate directory
- No duplicate content
- All links resolve

❌ **FAIL Criteria:**
- Missing status tag
- Generic name (e.g., `notes.md`, `stuff.md`)
- Duplicate of existing file
- In wrong directory for its purpose

---

### Repository Health

**Target Metrics:**

| Metric | Target | Measurement |
|--------|--------|-------------|
| Files with status tags | 95%+ | `scripts/audit_frontmatter.ps1` |
| Duplicate files | 0 | `scripts/identify_duplicates.ps1` |
| Broken links | 0 | `scripts/validate_links.ps1` |
| Avg file age (active) | <90 days | File metadata analysis |
| AI context pollution | <5% | Test prompt evaluation |

---

## 🚨 Red Flags - When to Intervene

### Immediate Action Required

🚨 **Multiple files with same name** (e.g., `spec (1).md`, `spec (2).md`)
→ **Action:** Deduplicate immediately

🚨 **Active code referencing archived files**
→ **Action:** Update imports or restore file from archive

🚨 **AI suggesting outdated patterns**
→ **Action:** Check if legacy files are improperly indexed

🚨 **New files without frontmatter**
→ **Action:** Add tags before merging PR

---

## 🔧 Quick Tools Reference

### Essential Scripts

```powershell
# Generate inventory
.\scripts\generate_inventory.ps1

# Find duplicates
.\scripts\identify_duplicates.ps1

# Validate links
.\scripts\validate_links.ps1

# Health check
.\scripts\directory_health_check.ps1

# Pre-commit validation
.\scripts\validate_new_file.ps1 -FilePath "path\to\file.md"
```

---

## 📞 Getting Help

**Questions about:**
- **Directory structure:** See `ARCHITECTURE.md`
- **File placement:** See `CLEANUP_REORGANIZATION_STRATEGY.md`
- **AI tool usage:** See tool-specific docs in `/docs/guides/`
- **Naming conventions:** See examples above

**Process questions:**
- Check `/docs/guides/` first
- Ask in team channel
- Update this guideline if answer isn't documented

---

## 📚 Related Documents

- [Full Cleanup Strategy](./CLEANUP_REORGANIZATION_STRATEGY.md) - Detailed multi-phase plan
- [Architecture Overview](./Complete AI Development Pipeline – Canonical Phase Plan/ARCHITECTURE.md) - System architecture
- [Implementation Summary](./Complete AI Development Pipeline – Canonical Phase Plan/pipeline_plus/IMPLEMENTATION_SUMMARY.md) - Current status

---

**Last Updated:** 2025-11-20
**Version:** 1.0
**Maintainer:** AI Systems Architect
**Review Frequency:** Quarterly

---

## 🎯 TL;DR - 5 Golden Rules

1. **Tag Everything** - Status, priority, source in frontmatter
2. **Isolate Archives** - Use `_archive/` with exclusion patterns
3. **Name Clearly** - `CATEGORY_SUBJECT_VERSION.ext`
4. **4 Layers Max** - Avoid deep directory nesting
5. **No Duplicates** - One canonical source per concept

**Remember:** The goal is AI clarity, not perfection. When in doubt, add a status tag and move on.

---

**END OF GUIDELINES**
