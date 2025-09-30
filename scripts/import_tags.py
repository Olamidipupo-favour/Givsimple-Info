#!/usr/bin/env python3
"""
CSV Tag Import Script

Usage: python scripts/import_tags.py path/to/tags.csv
"""

import sys
import csv
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from app.models import Tag, TagStatus
from app.utils.security import sanitize_input

def import_tags_from_csv(csv_file_path):
    """Import tags from CSV file"""
    app = create_app()
    
    with app.app_context():
        imported_count = 0
        skipped_count = 0
        errors = []
        
        try:
            with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    try:
                        token = sanitize_input(row.get('token', '').strip())
                        url = sanitize_input(row.get('url', '').strip())
                        
                        if not token or not url:
                            errors.append(f"Row {row_num}: Missing token or URL")
                            skipped_count += 1
                            continue
                        
                        # Validate token format
                        if len(token) < 8 or len(token) > 16 or not token.isalnum():
                            errors.append(f"Row {row_num}: Invalid token format '{token}'")
                            skipped_count += 1
                            continue
                        
                        # Check if token already exists
                        existing_tag = Tag.query.filter_by(token=token).first()
                        if existing_tag:
                            errors.append(f"Row {row_num}: Token '{token}' already exists")
                            skipped_count += 1
                            continue
                        
                        # Create new tag
                        tag = Tag(token=token, target_url=url, status=TagStatus.UNASSIGNED)
                        db.session.add(tag)
                        imported_count += 1
                        
                    except Exception as e:
                        errors.append(f"Row {row_num}: Error processing - {str(e)}")
                        skipped_count += 1
                
                db.session.commit()
                
                print(f"Import completed:")
                print(f"  - {imported_count} tags imported")
                print(f"  - {skipped_count} rows skipped")
                print(f"  - {len(errors)} errors")
                
                if errors:
                    print("\nErrors:")
                    for error in errors[:10]:  # Show first 10 errors
                        print(f"  - {error}")
                    if len(errors) > 10:
                        print(f"  ... and {len(errors) - 10} more errors")
                
        except FileNotFoundError:
            print(f"Error: File '{csv_file_path}' not found")
            return False
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return False
    
    return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/import_tags.py path/to/tags.csv")
        print("\nCSV format:")
        print("token,url")
        print("ABC123,https://cash.app/$user1")
        print("DEF456,https://paypal.me/user2")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"Error: File '{csv_file}' not found")
        sys.exit(1)
    
    success = import_tags_from_csv(csv_file)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
