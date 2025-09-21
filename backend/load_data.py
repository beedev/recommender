#!/usr/bin/env python3
"""
Simple script to load data into Neo4j with cleanup option
This runs the database loader with cleanup enabled for the new DB setup
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from data.loaders.database_loader import DatabaseLoader

def main():
    """Load data with cleanup for new DB setup"""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Neo4j configuration from environment
    neo4j_config = {
        'uri': os.getenv('NEO4J_URI'),
        'user': os.getenv('NEO4J_USERNAME'),
        'password': os.getenv('NEO4J_PASSWORD')
    }
    
    # Verify required config
    if not all(neo4j_config.values()):
        print("❌ Missing Neo4j configuration in .env file")
        print("Required: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD")
        sys.exit(1)
    
    print("🚀 Starting fresh database load with cleanup...")
    print(f"📡 Connecting to: {neo4j_config['uri']}")
    print(f"👤 User: {neo4j_config['user']}")
    
    try:
        # Create database loader
        loader = DatabaseLoader(
            neo4j_uri=neo4j_config['uri'],
            neo4j_user=neo4j_config['user'],
            neo4j_password=neo4j_config['password'],
            postgres_config=None,
            datasets_folder="../neo4j_datasets"
        )
        
        # Load all datasets with cleanup
        session = loader.load_all_datasets(
            validate_references=True,
            skip_existing=False,
            cleanup_first=True  # Clean up existing data first
        )
        
        # Generate final report
        report_file = Path(f"logs/database_loading_session_{session.session_id}.txt")
        report = loader.generate_session_report(report_file)
        
        print("\n" + report)
        
        if session.success:
            print("\n🎉 Database loading completed successfully!")
            print(f"📄 Detailed report: {report_file}")
            print("\n✅ Ready to test the welding recommendation system!")
            return True
        else:
            print("\n💥 Database loading completed with errors!")
            print(f"📄 Error report: {report_file}")
            return False
            
    except Exception as e:
        print(f"\n💥 Database loading failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)