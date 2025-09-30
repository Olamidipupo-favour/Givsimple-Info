#!/usr/bin/env python3
"""
CSV Tag Export Script

Usage: python scripts/export_tags.py
"""

import sys
import csv
from pathlib import Path
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from app.models import Tag

def export_tags_to_csv():
    """Export tags to CSV file"""
    app = create_app()
    
    with app.app_context():
        # Get all tags with their activations
        tags = Tag.query.all()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'givsimple_export_{timestamp}.csv'
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'token', 'status', 'target_url', 'buyer_name', 'buyer_email', 
                'buyer_phone', 'activation_date', 'payment_provider', 'payment_handle'
            ])
            
            for tag in tags:
                activation = tag.activations[0] if tag.activations else None
                buyer = tag.buyer
                
                writer.writerow([
                    tag.token,
                    tag.status.value,
                    tag.target_url or '',
                    buyer.name if buyer else '',
                    buyer.email if buyer else '',
                    buyer.phone if buyer else '',
                    activation.created_at.strftime('%Y-%m-%d %H:%M:%S') if activation else '',
                    activation.payment_provider.value if activation else '',
                    activation.payment_handle_or_url if activation else ''
                ])
        
        print(f"Export completed: {filename}")
        print(f"  - {len(tags)} tags exported")
        
        return filename

def main():
    try:
        filename = export_tags_to_csv()
        print(f"Export saved to: {filename}")
    except Exception as e:
        print(f"Error during export: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
