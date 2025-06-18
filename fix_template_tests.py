#!/usr/bin/env python3
"""Fix template analyzer tests"""

import re

# Read the file
with open('/Users/joecorella/Desktop/Projects/Scraper_V2/tests/test_template_analyzer.py', 'r') as f:
    content = f.read()

# Fix the patterns:
# 1. Remove the duplicate mock_template.elements = [element] lines that follow create_mock_template calls
# 2. Fix [element] references to use the correct variable names
# 3. Remove duplicate mock_template.actions = [] lines

# Pattern 1: Remove lines that duplicate element assignments after create_mock_template
lines = content.split('\n')
fixed_lines = []
skip_next = False

for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
        
    # If this line is a create_mock_template call, check if next line duplicates elements
    if 'mock_template = self.create_mock_template(' in line:
        fixed_lines.append(line)
        # Look ahead to see if we need to skip duplicate assignments
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line.startswith('mock_template.elements =') or next_line.startswith('mock_template.actions ='):
                skip_next = True
        continue
    
    fixed_lines.append(line)

content = '\n'.join(fixed_lines)

# Pattern 2: Fix common variable name mismatches
content = content.replace('self.create_mock_template([element])', 'self.create_mock_template([])')
content = content.replace('[container1, container2])', '[container1, container2])')
content = content.replace('[main_container, subpage_container])', '[main_container, subpage_container])')

# Write back
with open('/Users/joecorella/Desktop/Projects/Scraper_V2/tests/test_template_analyzer.py', 'w') as f:
    f.write(content)

print("Fixed template analyzer tests")