#!/usr/bin/env python
"""
Script to get emails of all players who want to participate in the season.
Usage: poetry run python get_season_participant_emails.py
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iglo.settings')
# Set the database port if needed (default is 15432 based on your setup)
os.environ.setdefault('IGLO_DB_PORT', '15432')

# Add the iglo directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'iglo'))

django.setup()

from league.models import Player


def get_participant_emails():
    """Get all emails of players who have auto_join set to True."""
    # Query all players with auto_join=True and their related user objects
    players_with_auto_join = Player.objects.filter(
        auto_join=True
    ).select_related('user')
    
    # Collect emails
    emails = []
    for player in players_with_auto_join:
        if player.user and player.user.email:
            emails.append(player.user.email)
    
    return sorted(emails)


def main():
    """Main function to run the script."""
    try:
        emails = get_participant_emails()
        
        print(f"Found {len(emails)} players with auto_join=True who have emails:")
        print("-" * 60)
        
        for email in emails:
            print(email)
        
        # Optionally save to file
        save_to_file = input("\nSave to file? (y/n): ").strip().lower()
        if save_to_file == 'y':
            filename = input("Enter filename (default: participant_emails.txt): ").strip()
            if not filename:
                filename = "participant_emails.txt"
            
            with open(filename, 'w') as f:
                f.write(f"Season Participant Emails ({len(emails)} total)\n")
                f.write("=" * 60 + "\n\n")
                for email in emails:
                    f.write(email + "\n")
            
            print(f"\nEmails saved to {filename}")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()