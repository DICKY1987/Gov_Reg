#!/usr/bin/env python3
"""Execute file moves from MOVE_MAP.json"""
import json
import shutil
from pathlib import Path
import sys

def execute_moves(move_map_path: str, dry_run: bool = True):
    """Execute file moves from the move map"""
    
    # Load move map
    with open(move_map_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    moves = data.get('moves', [])
    eligible = [m for m in moves if m.get('eligible', False)]
    
    print(f"Total moves in plan: {len(moves)}")
    print(f"Eligible moves: {len(eligible)}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE EXECUTION'}")
    print("=" * 60)
    
    if not eligible:
        print("No eligible moves to execute.")
        return
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for i, move in enumerate(eligible, 1):
        source = Path(move['source_abs_path'])
        dest = Path(move['dest_abs_path'])
        category = move.get('category', 'UNKNOWN')
        
        print(f"\n[{i}/{len(eligible)}] {category}")
        print(f"  FROM: {source.name}")
        print(f"  TO:   {dest.parent.name}\\{dest.name}")
        
        # Check if source exists
        if not source.exists():
            print(f"  ❌ SKIP: Source file does not exist")
            skipped_count += 1
            continue
        
        # Check if destination already exists
        if dest.exists():
            print(f"  ❌ SKIP: Destination already exists")
            skipped_count += 1
            continue
        
        # Ensure destination directory exists
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if dry_run:
                print(f"  ✓ Would move")
            else:
                shutil.move(str(source), str(dest))
                print(f"  ✅ MOVED")
            success_count += 1
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            error_count += 1
    
    print("\n" + "=" * 60)
    print(f"SUMMARY:")
    print(f"  Success: {success_count}")
    print(f"  Errors:  {error_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Total:   {len(eligible)}")
    
    if dry_run:
        print("\n⚠️  This was a DRY RUN - no files were moved.")
        print("To execute for real, run: python execute_moves.py --execute")

if __name__ == '__main__':
    move_map = Path(__file__).parent / 'MOVE_MAP.json'
    
    if not move_map.exists():
        print(f"Error: {move_map} not found")
        sys.exit(1)
    
    # Check for --execute flag
    dry_run = '--execute' not in sys.argv
    
    execute_moves(str(move_map), dry_run=dry_run)
