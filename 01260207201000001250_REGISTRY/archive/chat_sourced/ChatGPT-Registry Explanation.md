# Registry Explanation

**User:** bill reed (richgwilks@gmail.com)  
**Created:** 2/21/2026 16:15:00  
**Updated:** 2/22/2026 0:50:48  
**Exported:** 2/22/2026 17:02:56  
**Link:** [https://chatgpt.com/g/g-p-690ce579540c8191a83eb108945f7da9-id-sub-module/c/699a2e5a-9ce8-832e-9c19-91ff39738404](https://chatgpt.com/g/g-p-690ce579540c8191a83eb108945f7da9-id-sub-module/c/699a2e5a-9ce8-832e-9c19-91ff39738404)  

## Response:
Thought for 41s

What “the registry” is
----------------------

The registry is the project’s **Single Source of Truth (SSOT)** for your workspace. It’s a **machine-readable inventory** of every governed file (and sometimes directories) with a **stable 20-digit `file_id`**, plus governance metadata (classification, roles, ownership) and relationship links (“this validator enforces that schema”, “this runner executes that gate”, etc.).

01999000042260124503\_REGISTRY\_f…

* * *

What’s inside it
----------------

### 1) File records (entities)

A file record is one row/object per file, keyed by `file_id` (20 digits). The governance registry schema requires a core minimum so every file can be resolved and classified deterministically: `file_id`, `relative_path`, `repo_root_id`, `governance_domain`, `artifact_kind`, `layer`, `canonicality`, `has_tests`, plus optional fields like `sha256`, `dir_id`, bundle and GEU assignments, dependency lists, etc.

01999000042260124012\_governance…

### 2) Edges (relationships)

Edges connect files to other files (or to schemas) with a typed relationship such as `VALIDATES`, `EXECUTES`, `DEPENDS_ON`, `TESTS`, `COLLECTS_EVIDENCE`, etc., and each edge carries an **evidence record** (what proved the relationship and whether it’s proven).

01999000042260124012\_governance…

* * *

Columns: “registry headers” vs “column dictionary”
--------------------------------------------------

You have two related but different things:

### A) Registry column headers (the implemented subset)

Your governance registry is currently described as having a **defined set of columns** (27 in the column header reference) grouped into Identity/Location, Classification, GEU fields, Bundle fields, Dependencies/Relationships, Testing/Evidence, and Status.

REGISTRY\_COLUMN\_HEADERS

### B) Column dictionary (the full contract catalog)

The column dictionary is the **master specification** of _all possible headers_ and how each header behaves:

*   type constraints (`value_schema`)
*   when it applies (`scope`, conditional presence rules)
*   normalization transforms
*   provenance (where the definition comes from)
*   derivation rules and required evidence for derived fields

It also declares an **expected header count** much larger than the registry’s current subset (e.g., 184 expected headers in the dictionary you surfaced).

01260207233100000463\_2026012816…

**Bottom line:** the column dictionary is the **superset contract**; the registry often stores a **projection** (subset) that can expand over time without losing determinism.

* * *

How the registry is updated (deterministic ingestion)
-----------------------------------------------------

Your ingest spec describes a deterministic pipeline that turns a filesystem observation into a registry write:

*   Load contracts (column dictionary + write policy + derivations + schema)
*   Build file context from filesystem (paths, timestamps, type, etc.)
*   Select applicable headers and sort by dependency order
*   Resolve identity:
    *   use existing 20-digit prefix if valid, else allocate a new `file_id`
*   Populate fields in phases (identity → scan → inference → optional python-analysis fields)
*   Write using **RFC-6902 patch** and a **single-writer atomic commit** path
*   Emit an evidence bundle for auditability and rollback if needed
    01260202173939000111\_INGEST\_SPE…

* * *

How GEUs fit in
---------------

A GEU (Governance Enforcement Unit) is a governed “bundle” of files playing roles like `SCHEMA`, `RULE`, `VALIDATOR`, `RUNNER`, `FAILURE_MODE`, `EVIDENCE`, `TEST`, `REPORT`. The registry defines role semantics and a “slot matrix” of what roles are required for different GEU types.

01999000042260124503\_REGISTRY\_f…

Your GEU sets analysis shows the registry can group files by GEU and role, giving you a completeness view of each enforcement unit (what’s missing, duplicated, etc.).

01260207201000000854\_GEU\_SETS\_A…

## Response:
Thought for 4m 57s

Thought for 2m 16s

Download CSV  
Download Markdown

Note: the dictionary file defines **185** header definitions, but `header_order` contains the **184** headers below. The extra defined header is `dir_id` (20-digit directory identifier from a parent `.dir_id` file), but it is not in `header_order`.

1.  **absolute\_path** — Absolute filesystem path to the file at scan time.
2.  **allocated\_at** — UTC timestamp when the file\_id was allocated.
3.  **anchor\_file\_id** — File\_id used as the anchor/primary key for a parent record/document context.
4.  **artifact\_kind** — Artifact category (e.g., doc, schema, script, config, report).
5.  **asset\_family** — Asset grouping/family label (for non-code assets).
6.  **asset\_id** — Identifier for an asset entity (when the record represents an asset).
7.  **asset\_version** — Version string/number for an asset.
8.  **build\_report\_entity\_id** — Entity\_id of the build/report record produced by a generator run.
9.  **bundle\_id** — 16-digit numeric identifier for bundle grouping
10.  **bundle\_key** — Human-readable stable bundle name (e.g., GATE\_AGGREGATE, ID\_REGISTRY)
11.  **bundle\_role** — Bundle member role (e.g., SCHEMA, VALIDATOR, RUNNER, REPORT)
12.  **bundle\_version** — Bundle semantic version (e.g., 1.0.0)
13.  **canonical\_path** — Normalized/canonicalized path (normalized slashes + canonical rules).
14.  **canonicality** — Canonicality status (canonical vs duplicate/alias).
15.  **collected\_by** — Tool/process identifier that collected or produced the record/field.
16.  **column\_headers** — List of column headers present in a structured document/registry payload.
17.  **confidence** — Confidence score for an edge/relationship assertion.
18.  **content\_type** — Content/type classification (often extension/MIME-like or format class).
19.  **contracts\_consumed** — Contracts/specs this entity/process consumed as inputs.
20.  **contracts\_produced** — Contracts/specs this entity/process produced as outputs.
21.  **coverage\_status** — Test/coverage status label for the file/module.
22.  **created\_by** — Identifier of who/what created the record (user/tool).
23.  **created\_utc** — UTC timestamp when the record was created.
24.  **data\_transformation** — Transformation descriptor (reserved/placeholder for transformation pipeline metadata).
25.  **declared\_dependencies** — Dependencies explicitly declared by the artifact (e.g., imports, requires).
26.  **deliverables** — Deliverables produced/owned by this entity/process (IDs or descriptors).
27.  **depends\_on\_file\_ids** — List of file\_ids this entity depends on.
28.  **description** — Human-readable description of the entity/record.
29.  **directionality** — Directionality of an edge (source→target semantics).
30.  **directory\_path** — Directory portion of the file path.
31.  **edge\_flags** — Flags/markers on an edge (e.g., inferred, manual, low\_confidence).
32.  **edge\_id** — Unique identifier for an edge record.
33.  **edge\_type** — Edge/relationship type classifier (high-level).
34.  **edges** — Collection of edge records associated with an entity.
35.  **enforced\_by** — Human-readable/enumerated enforcement reference (who enforces this).
36.  **enforced\_by\_file\_ids** — File\_ids of enforcers (validators/runners) for this entity.
37.  **enforces** — Human-readable/enumerated enforcement target (what this enforces).
38.  **enforces\_rule\_ids** — Rule IDs enforced by this artifact.
39.  **entity\_id** — Internal entity record identifier (registry record ID, not the 20-digit file\_id).
40.  **entity\_kind** — Kind of entity (file, asset, transient, external, etc.).
41.  **entries** — Collection of ‘entries’ records (often registry sub-section).
42.  **entrypoint\_flag** — Flag indicating the file is an executable entrypoint (CLI/main/etc.).
43.  **evidence** — Evidence object/structure supporting a claim/field/edge.
44.  **evidence\_locator** — Pointer/locator to the evidence artifact (path/id).
45.  **evidence\_method** — How evidence was obtained (scanner, parser, manual, etc.).
46.  **evidence\_only** — Boolean indicating the artifact/GEU is evidence-only (not enforcement logic).
47.  **evidence\_outputs** — Evidence artifacts produced by a run/process.
48.  **evidence\_snippet** — Short snippet/summary excerpt captured as evidence (if allowed).
49.  **evidence\_type** — Type/class of evidence artifact.
50.  **expires\_utc** — UTC expiration timestamp (primarily for transient records).
51.  **extension** — Lowercased file extension (without path).
52.  **external\_ref** — Reference/identifier in an external system.
53.  **external\_system** — Name of the external system the reference belongs to.
54.  **extract** — Extracted structured payload produced from parsing/analysis.
55.  **file\_id** — Stable 20-digit identifier assigned to the file.
56.  **filename** — File name (typically including the ID prefix in your system).
57.  **files** — Collection of ‘files’ records (often registry sub-section).
58.  **first\_seen\_utc** — First time (UTC) the file was observed in scans.
59.  **function\_code\_1** — Functional classification code 1 (project-specific taxonomy).
60.  **function\_code\_2** — Functional classification code 2 (project-specific taxonomy).
61.  **function\_code\_3** — Functional classification code 3 (project-specific taxonomy).
62.  **generated** — Whether a record/document was generated by a tool vs authored manually.
63.  **generated\_at** — UTC timestamp when a generated artifact/section was produced.
64.  **generated\_by\_file\_id** — File\_id of the generator script/tool that produced this artifact.
65.  **generator\_id** — Identifier of a generator record (build/emitter).
66.  **generator\_name** — Human-readable generator name.
67.  **generator\_version** — Generator version string.
68.  **geu\_ids** — List of GEU IDs this file/entity participates in.
69.  **geu\_role** — GEU role assigned to the file within a GEU.
70.  **geu\_role\_definitions** — Role definitions (looked up from GEU registry) relevant to this file/GEU.
71.  **geu\_type\_slot\_matrix** — Definition of required/optional roles per GEU type (slot matrix).
72.  **governance\_domain** — Governance domain/category for the entity (e.g., REGISTRY/ID/CLI/etc.).
73.  **has\_tests** — Boolean indicating whether the file has associated tests.
74.  **input\_filters** — Filters used by a generator/validator to select inputs.
75.  **inputs** — Input artifacts/refs for a process/generator.
76.  **is\_directory** — Boolean flag indicating the entity is a directory.
77.  **is\_generated** — Boolean indicating the file/artifact is generated (non-handwritten) output.
78.  **is\_shared** — Boolean indicating shared/common artifact across modules/domains.
79.  **last\_build\_utc** — UTC time of last generator/build producing the output.
80.  **last\_seen\_utc** — Most recent time (UTC) the file was observed in scans.
81.  **layer** — Architecture layer classification (project-specific).
82.  **metadata** — Freeform metadata object (structured key/value).
83.  **module\_id** — Assigned module identifier for the file.
84.  **module\_id\_override** — Manual override for module assignment.
85.  **module\_id\_source** — Where module\_id came from (rule/override/inferred/etc.).
86.  **mtime\_utc** — Filesystem last-modified time (UTC).
87.  **notes** — Freeform notes for humans/analysts.
88.  **ns\_code** — Namespace code used by the ID system (project-specific).
89.  **observed\_utc** — UTC time an edge/relationship observation was made.
90.  **one\_line\_purpose** — Single-line purpose statement for the file.
91.  **optional\_roles** — Optional GEU roles allowed for the GEU type / requirement set.
92.  **output\_hash** — Hash of generator output (integrity/determinism).
93.  **output\_kind** — Output artifact kind/type produced by a generator.
94.  **output\_path** — Path where a generator wrote an output artifact.
95.  **output\_path\_pattern** — Pattern/template for output paths used by a generator.
96.  **outputs** — Output artifacts/refs for a process/generator.
97.  **owner\_geu\_id** — GEU ID that ‘owns’ the file (primary ownership assignment).
98.  **path\_aliases** — Alternate/previous paths for the file (renames/moves).
99.  **primary\_geu\_id** — Primary GEU assignment (main GEU for the file).
100.  **process\_id** — Process identifier associated with the file (e.g., phase/workstream process).
101.  **process\_step\_id** — Identifier of the process step associated with the file.
102.  **process\_step\_role** — Role of the file in a specific process step.
103.  **py\_analysis\_run\_id** — Unique identifier for the Python analysis run
104.  **py\_analysis\_success** — Whether the Python analysis completed successfully
105.  **py\_analyzed\_at\_utc** — Timestamp (UTC) when the Python analysis was performed
106.  **py\_ast\_dump\_hash** — Hash of the normalized AST dump for the Python file
107.  **py\_ast\_parse\_ok** — Whether the Python file parsed successfully into an AST
108.  **py\_canonical\_candidate\_score** — Score indicating how likely this file is a canonical implementation
109.  **py\_canonical\_text\_hash** — Hash of normalized Python source text (whitespace/format normalized)
110.  **py\_capability\_facts\_hash** — Hash of extracted capability facts for the Python file
111.  **py\_capability\_tags** — List of derived capability tags for the Python file
112.  **py\_complexity\_cyclomatic** — Cyclomatic complexity estimate
113.  **py\_component\_artifact\_path** — Path to a generated component artifact (if produced)
114.  **py\_component\_count** — Number of components detected in the Python file
115.  **py\_component\_ids** — List of component identifiers detected in the Python file
116.  **py\_coverage\_percent** — Test coverage percentage attributed to the Python file/module
117.  **py\_defs\_classes\_count** — Count of class definitions
118.  **py\_defs\_functions\_count** — Count of function definitions
119.  **py\_defs\_public\_api\_hash** — Hash representing the detected public API surface
120.  **py\_deliverable\_inputs** — Declared/derived inputs for the file’s deliverable interface
121.  **py\_deliverable\_interfaces** — Detected deliverable interfaces (APIs/CLIs/hooks)
122.  **py\_deliverable\_kinds** — Deliverable kinds produced/represented (e.g., CLI, LIB, SERVICE)
123.  **py\_deliverable\_outputs** — Declared/derived outputs for the file’s deliverable interface
124.  **py\_deliverable\_signature\_hash** — Hash of deliverable signature (interfaces + I/O) for change detection
125.  **py\_imports\_hash** — Hash of import graph summary for the file
126.  **py\_imports\_local** — List of local/project imports detected
127.  **py\_imports\_stdlib** — List of Python standard library imports detected
128.  **py\_imports\_third\_party** — List of third-party imports detected
129.  **py\_io\_surface\_flags** — Flags indicating I/O surface (filesystem, network, subprocess, etc.)
130.  **py\_overlap\_best\_match\_file\_id** — File\_id of most similar/overlapping Python file (dedup/canonicality)
131.  **py\_overlap\_group\_id** — Group identifier for overlap cluster
132.  **py\_overlap\_similarity\_max** — Maximum similarity score found during overlap analysis
133.  **py\_pytest\_exit\_code** — Exit code from pytest execution (if run)
134.  **py\_quality\_score** — Aggregate Python quality score (project-defined)
135.  **py\_security\_risk\_flags** — Flags for detected security risk patterns
136.  **py\_static\_issues\_count** — Count of static analysis issues detected
137.  **py\_tests\_executed** — Whether tests were executed for this file during analysis
138.  **py\_tool\_versions** — Tool versions used during analysis (linters/parsers/etc.)
139.  **py\_toolchain\_id** — Identifier for the analysis toolchain configuration
140.  **record\_id** — Unique record identifier across record kinds.
141.  **record\_kind** — Record kind discriminator (entity/edge/generator/etc.).
142.  **rel\_type** — Relationship type (edge semantic type, e.g., DEPENDS\_ON/VALIDATES).
143.  **relative\_path** — Repo-relative path to the file.
144.  **repo\_root\_id** — Identifier for the repository root/context this record belongs to.
145.  **report\_outputs** — Report artifacts produced (paths/IDs).
146.  **required\_roles** — Required GEU roles for the GEU type / requirement set.
147.  **required\_suite\_key** — Key identifying a required test/validation suite.
148.  **resolver\_hint** — Hint used by resolvers/mappers for disambiguation/linking.
149.  **role** — Role label for the file/entity (project taxonomy).
150.  **role\_code** — Role code for the file/entity (project taxonomy).
151.  **rule\_based** — Whether the GEU enforces using a rule (as opposed to runner/schema)
152.  **runner\_based** — Whether the GEU enforces using a runner/executor
153.  **scan\_id** — Identifier of the scan run that produced/updated the record.
154.  **schema\_based** — Whether the GEU enforces using a schema
155.  **schema\_version** — Schema version identifier used for validation/structure.
156.  **scope** — Scope definition for where a field applies (record/entity kinds).
157.  **sha256** — SHA-256 hash of the file contents.
158.  **short\_description** — Short description (compact summary).
159.  **size\_bytes** — File size in bytes.
160.  **sort\_keys** — List of keys used to deterministically sort outputs (tables/records).
161.  **sort\_rule\_id** — Identifier of the sorting rule applied.
162.  **source\_entity\_id** — Source-side entity\_id for an edge relationship.
163.  **source\_file\_id** — Source-side file\_id for an edge relationship.
164.  **source\_registry\_hash** — Hash of the source registry snapshot used as input.
165.  **source\_registry\_scan\_id** — Scan/build ID corresponding to the source registry snapshot.
166.  **status** — Lifecycle status (active/deprecated/archived/etc.).
167.  **step\_refs** — References/IDs of steps (phase/workstream/gate steps) linked to the file.
168.  **superseded\_by** — Identifier of the artifact that supersedes this one.
169.  **supersedes\_entity\_id** — Entity\_id that this artifact supersedes (version lineage).
170.  **tags** — Tags/labels (searchable categorical metadata).
171.  **target\_entity\_id** — Target-side entity\_id for an edge relationship.
172.  **target\_file\_id** — Target-side file\_id for an edge relationship.
173.  **target\_schema\_id** — Schema identifier referenced/targeted by the entity/edge.
174.  **template\_ref\_entity\_id** — Entity\_id reference to a template record used/produced.
175.  **test\_file\_ids** — File\_ids of test files associated with the entity.
176.  **tool\_version** — Version of the tool that produced the record/edge.
177.  **transient\_id** — Identifier for a transient record (non-permanent entity).
178.  **transient\_type** — Type/class of transient record.
179.  **ttl\_seconds** — Time-to-live in seconds for a transient record.
180.  **type\_code** — Type code used by the ID system (project-specific).
181.  **updated\_by** — Identifier of who/what last updated the record.
182.  **updated\_utc** — UTC timestamp when the record was last updated.
183.  **validation\_rules** — Validation rule set applied/required (often on generator records).
184.  **validator\_id** — Identifier of a validator record/tool.

## Response:
Thought for 4m 36s

Yes. There’s real overlap, plus a few structural problems that will cause drift or broken projections.

Overlap / redundancy in headers
-------------------------------

### 1) Same concept, two headers

*   **`edge_type` vs `rel_type`**  
    Both are “relationship type”. `rel_type` is the one that’s _scoped to edge_ and has an enum; `edge_type` is unscoped/optional and will drift. Pick **one** (recommend: keep `rel_type`, deprecate `edge_type`).
*   **`generated` vs `is_generated`**  
    Both are boolean “generated-ness” with no enforced distinction. This will split truth across two columns unless you define hard semantics (or delete one).
*   **`entity_kind` vs `is_directory`**  
    `entity_kind` already includes `directory`. `is_directory` becomes redundant unless you explicitly define it as a derived convenience flag (and then don’t store it, derive it).

### 2) Same intent, multiple “description” columns

*   **`description` / `short_description` / `one_line_purpose` / `notes`**  
    Without strict rules, these become four competing “explain this file” fields. You need a clear contract like:
    *   `one_line_purpose`: required for governed files, ≤120 chars
    *   `short_description`: optional, ≤500 chars
    *   `description`: optional, long-form
    *   `notes`: analyst notes only, never used as “purpose”

### 3) ID fields that will confuse consumers

*   **`record_id` vs `entity_id` vs `file_id` vs `edge_id` vs `generator_id`**  
    This is fine only if you hard-separate record kinds. If you keep a single wide table, users will mix them up. Usually:
    *   `record_id`: universal primary key for all records
    *   `record_kind`: discriminator
    *   then _exactly one_ of (`file_id`, `edge_id`, `generator_id`, `transient_id`, etc.) depending on `record_kind`

### 4) Paths overlap unless you define precedence

*   **`absolute_path`, `relative_path`, `canonical_path`, `directory_path`, `filename`, `path_aliases`**  
    These can all be valid, but you must define:
    *   which is authoritative (`relative_path` usually)
    *   which are derived (`directory_path`, `filename`)
    *   how `canonical_path` differs from `relative_path`
    *   how `path_aliases` is populated (moves/renames only, append-only, etc.)

### 5) Test/coverage overlap (general vs Python-specific)

*   General: `has_tests`, `test_file_ids`, `coverage_status`
*   Python-specific: `py_tests_executed`, `py_pytest_exit_code`, `py_coverage_percent`  
    Without a rule, you’ll get contradictory states (“has\_tests=false” while `py_tests_executed=true`). You need a precedence rule or derive general fields from language-specific evidence.

Other issues with the list
--------------------------

### A) Defined-but-not-emitted header

*   The dictionary defines **`dir_id`**, but it is **not in `header_order`**. That means any emitter/normalizer driven by `header_order` will silently ignore `dir_id`.

### B) Scope problems (this is a big one)

*   **40 headers have an empty `record_kinds_in` scope** (and empty `entity_kinds_in`). For several columns, that’s almost certainly wrong because they are obviously edge-only or doc-container fields. High-risk examples:
    *   Edge-ish but unscoped: `source_file_id`, `target_file_id`, `target_schema_id`, `edge_type`
    *   Container-ish (not a flat column at all): `files`, `entries`, `edges`
    *   Generator-ish but unscoped: `inputs`, `outputs`, `report_outputs`
    *   Evidence-ish but unscoped: `evidence`, `evidence_type`, `evidence_outputs`  
        If you don’t fix this, different tools will project these headers into places they don’t belong, especially if you ever serialize to CSV/Excel.

### C) “core” appears in scopes, but isn’t a valid record\_kind

*   9 fields use `record_kinds_in: ['core', ...]` (e.g., `record_id`, `record_kind`, `status`, timestamps, etc.), but `record_kind`’s enum is only `entity|edge|generator`. Either:
    *   add `core` to `record_kind`, **or**
    *   remove `core` from scopes and treat these as shared fields across the existing kinds.

### D) `status` enum mixes two different concepts

`status` includes both lifecycle states (`active`, `archived`, `deprecated`, …) and runtime/process outcomes (`running`, `pending`, `failed`). That guarantees misuse. Split it:

*   `lifecycle_status` (file/entity lifecycle)
*   `run_status` (generator/process run outcome)  
    or scope the allowed enum values by `record_kind` / `entity_kind`.

### E) Type looseness that invites garbage

*   `data_transformation` allows **boolean|string|null**. That’s a schema smell. Make it either a structured object (preferred) or a single string enum.

### F) Too many array/object fields for a “flat registry” without encoding rules

You have **35 array** fields and **6 object** fields. If any consumer expects a flat table, you need a deterministic serialization rule (stable ordering + sorted keys) or split records by kind into separate registries (entity table, edge table, generator table).

What to fix first (minimal, high-impact)
----------------------------------------

1.  Decide whether the registry is **multi-record-kind JSON** or a **flat table**. Don’t pretend it’s both.
2.  Tighten scopes for the 18 high-risk unscoped fields listed above.
3.  Canonicalize overlaps: `edge_type→rel_type`, `generated/is_generated`, `entity_kind/is_directory`.
4.  Split or scope `status`.
5.  Add `dir_id` to `header_order` (or delete it from the dictionary if you’re not using it).



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)