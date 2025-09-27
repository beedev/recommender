#!/bin/bash

# Restoration Script for Current Data Model (September 25, 2025)
# Run this script to restore to the working state before architectural changes

echo "🔄 Restoring to September 25, 2025 data model state..."

# Navigate to project root
cd /Users/bharath/Desktop/AgenticAI/Recommender

# Restore source data
echo "📁 Restoring source data files..."
rm -rf neo4j_datasets
rm -rf neo4jdatasets  
cp -r Datamodel_Backup_September25_2025/neo4j_datasets_backup neo4j_datasets
cp -r Datamodel_Backup_September25_2025/neo4jdatasets_backup neo4jdatasets

# Restore loader code
echo "💻 Restoring loader code..."
rm -rf backend/data/loaders
cp -r Datamodel_Backup_September25_2025/loaders_backup backend/data/loaders

# Reload database
echo "🗄️  Reloading database with restored code and data..."
cd backend
python load_data.py

echo "✅ Restoration completed!"
echo "🔍 Verify by testing: curl -X POST 'http://localhost:8000/api/v1/enterprise/recommendations' ..."
echo "📊 Check Trinity relationships: 19 unique combinations, 11,087 total relationships"
echo "🎯 Intent match bonus should work for 'package with Renegade' queries"