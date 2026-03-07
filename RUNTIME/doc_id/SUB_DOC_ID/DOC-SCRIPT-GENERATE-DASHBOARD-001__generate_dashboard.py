#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-GENERATE-DASHBOARD-001
"""
Generate unified dashboard HTML from ID_TYPE_REGISTRY.yaml
DOC_ID: DOC-SCRIPT-GENERATE-DASHBOARD-001
"""

import yaml
import json
from pathlib import Path
from datetime import datetime

def load_registry():
    """Load ID type registry"""
    registry_path = Path(__file__).parent / "ID_TYPE_REGISTRY.yaml"
    with open(registry_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_id_counts():
    """Load actual ID counts from registries"""
    counts = {}
    base = Path(__file__).parent

    # doc_id
    doc_reg = base / "5_REGISTRY_DATA" / "DOC_ID_REGISTRY.yaml"
    if doc_reg.exists():
        with open(doc_reg, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            counts['doc_id'] = len(data.get('documents', []))

    # trigger_id
    trg_reg = base / "trigger_id" / "5_REGISTRY_DATA" / "TRG_ID_REGISTRY.yaml"
    if trg_reg.exists():
        with open(trg_reg, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            counts['trigger_id'] = len(data.get('triggers', []))

    # pattern_id
    pat_reg = base / "pattern_id" / "5_REGISTRY_DATA" / "PAT_ID_REGISTRY.yaml"
    if pat_reg.exists():
        with open(pat_reg, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            counts['pattern_id'] = len(data.get('patterns', []))

    return counts

def generate_html(registry, counts):
    """Generate dashboard HTML"""

    # Calculate statistics
    total_types = registry.get('meta', {}).get('total_types', 0)
    by_status = registry.get('meta', {}).get('by_status', {})

    production_types = [t for t in registry.get('id_types', []) if t.get('status') == 'production']
    production_count = len(production_types)

    total_ids = sum(counts.values())

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unified Stable ID Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }}

        h1 {{
            font-size: 3em;
            margin-bottom: 10px;
        }}

        .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}

        .stat-label {{
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}

        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 4px;
        }}

        .stat-value.production {{
            color: #10b981;
        }}

        .stat-value.planned {{
            color: #3b82f6;
        }}

        .stat-sublabel {{
            font-size: 0.85em;
            color: #999;
        }}

        .types-section {{
            background: white;
            border-radius: 12px;
            padding: 32px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}

        .section-title {{
            font-size: 1.8em;
            margin-bottom: 24px;
            color: #333;
        }}

        .type-card {{
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
        }}

        .type-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
        }}

        .type-name {{
            font-size: 1.3em;
            font-weight: 600;
            color: #111;
        }}

        .type-id {{
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            color: #6366f1;
            margin-top: 4px;
        }}

        .type-status {{
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .type-status.production {{
            background: #d1fae5;
            color: #065f46;
        }}

        .type-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin-top: 16px;
        }}

        .type-stat {{
            text-align: center;
            padding: 12px;
            background: #f9fafb;
            border-radius: 6px;
        }}

        .type-stat-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #10b981;
        }}

        .type-stat-label {{
            font-size: 0.85em;
            color: #6b7280;
            margin-top: 4px;
        }}

        .updated {{
            text-align: center;
            color: white;
            margin-top: 40px;
            opacity: 0.8;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎯 Unified Stable ID Dashboard</h1>
            <p class="subtitle">Real-time monitoring of all ID types across the system</p>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total ID Types</div>
                <div class="stat-value production">{total_types}</div>
                <div class="stat-sublabel">Registered in meta-registry</div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Production</div>
                <div class="stat-value production">{production_count}</div>
                <div class="stat-sublabel">Fully operational</div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Total IDs</div>
                <div class="stat-value production">{total_ids:,}</div>
                <div class="stat-sublabel">Across all production types</div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Planned</div>
                <div class="stat-value planned">{by_status.get('planned', 0)}</div>
                <div class="stat-sublabel">Ready for implementation</div>
            </div>
        </div>

        <div class="types-section">
            <h2 class="section-title">Production ID Types</h2>
"""

    # Add production types
    for id_type in production_types:
        type_id = id_type.get('type_id')
        name = id_type.get('name', type_id)
        format_str = id_type.get('format', 'N/A')
        count = counts.get(type_id, id_type.get('coverage', {}).get('total_ids', 0))
        coverage = id_type.get('coverage', {}).get('percentage', 0)

        html += f"""
            <div class="type-card">
                <div class="type-header">
                    <div>
                        <div class="type-name">{name}</div>
                        <div class="type-id">{type_id}</div>
                    </div>
                    <div class="type-status production">Production</div>
                </div>
                <div class="type-stats">
                    <div class="type-stat">
                        <div class="type-stat-value">{count}</div>
                        <div class="type-stat-label">Total IDs</div>
                    </div>
                    <div class="type-stat">
                        <div class="type-stat-value">{coverage:.0f}%</div>
                        <div class="type-stat-label">Coverage</div>
                    </div>
                    <div class="type-stat">
                        <div class="type-stat-value">{len(id_type.get('validators', []))}</div>
                        <div class="type-stat-label">Validators</div>
                    </div>
                </div>
                <div style="margin-top: 12px; font-size: 0.9em; color: #6b7280;">
                    Format: <code style="background: #f3f4f6; padding: 2px 6px; border-radius: 4px;">{format_str}</code>
                </div>
            </div>
"""

    html += f"""
        </div>

        <div class="updated">
            Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""

    return html

def main():
    """Generate and save dashboard"""
    print("📊 Generating unified dashboard...")

    registry = load_registry()
    counts = load_id_counts()

    html = generate_html(registry, counts)

    output_path = Path(__file__).parent / "unified_dashboard.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Dashboard generated: {output_path}")
    print(f"   Total types: {registry.get('meta', {}).get('total_types', 0)}")
    print(f"   Total IDs: {sum(counts.values())}")

if __name__ == '__main__':
    main()
