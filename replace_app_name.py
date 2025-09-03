#!/usr/bin/env python3
"""
Script to replace <APP_NAME> placeholder with actual app name.
Usage: python3 replace_app_name.py <new_app_name>
"""

import os
import sys
import re
from pathlib import Path


def replace_app_name(old_name: str, new_name: str, project_root: Path):
    """Replace app name in all relevant files."""
    
    # Files to update
    files_to_update = [
        'config/settings.py',
        'config/urls.py',
        'docker-compose.yml',
        'MONITOR_README.md',
    ]
    
    # Directories to rename
    if old_name != new_name and (project_root / old_name).exists():
        old_dir = project_root / old_name
        new_dir = project_root / new_name
        
        print(f"Renaming directory: {old_dir} -> {new_dir}")
        old_dir.rename(new_dir)
        
        # Update files inside the renamed directory
        for py_file in new_dir.rglob("*.py"):
            update_file(py_file, old_name, new_name)
    
    # Update other files
    for file_path in files_to_update:
        full_path = project_root / file_path
        if full_path.exists():
            update_file(full_path, old_name, new_name)
    
    print(f"✅ Successfully replaced '{old_name}' with '{new_name}'")
    print(f"📝 Don't forget to update your INSTALLED_APPS and URL imports!")


def update_file(file_path: Path, old_name: str, new_name: str):
    """Update a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace app name references
        patterns = [
            (f"'{old_name}'", f"'{new_name}'"),
            (f'"{old_name}"', f'"{new_name}"'),
            (f'{old_name}.', f'{new_name}.'),
            (f'from {old_name}', f'from {new_name}'),
            (f'import {old_name}', f'import {new_name}'),
            (f'include(\'{old_name}', f'include(\'{new_name}'),
        ]
        
        updated = False
        for old_pattern, new_pattern in patterns:
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
                updated = True
        
        if updated:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ Updated: {file_path}")
    
    except Exception as e:
        print(f"  ✗ Error updating {file_path}: {e}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 replace_app_name.py <new_app_name>")
        print("Example: python3 replace_app_name.py healthmonitor")
        sys.exit(1)
    
    new_name = sys.argv[1]
    
    # Validate app name
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', new_name):
        print("❌ Invalid app name. Use only letters, numbers, and underscores.")
        sys.exit(1)
    
    project_root = Path(__file__).parent
    old_name = "monitor"  # Current app name
    
    print(f"🔄 Replacing app name from '{old_name}' to '{new_name}'...")
    replace_app_name(old_name, new_name, project_root)


if __name__ == '__main__':
    main()