#!/usr/bin/env python3
"""
PowerSource System Validation Script
Validates system prerequisites and configuration before extraction
"""

import json
import sys
from pathlib import Path
import pandas as pd
from typing import List, Dict, Tuple

def print_status(message: str, status: str = "INFO"):
    colors = {
        "INFO": "\033[0;32m",    # Green
        "WARN": "\033[1;33m",    # Yellow  
        "ERROR": "\033[0;31m",   # Red
        "HEADER": "\033[0;34m"   # Blue
    }
    reset = "\033[0m"
    print(f"{colors.get(status, '')}[{status}]{reset} {message}")

def check_file_exists(file_path: Path, description: str) -> bool:
    """Check if a file exists and report status"""
    if file_path.exists():
        print_status(f"✅ {description}: {file_path}")
        return True
    else:
        print_status(f"❌ {description} missing: {file_path}", "ERROR")
        return False

def validate_powersource_gin(gin: str) -> bool:
    """Validate PowerSource GIN format"""
    if not gin or len(gin) != 10:
        return False
    if not gin.isdigit():
        return False
    return True

def validate_config_file(config_path: Path) -> Tuple[bool, Dict]:
    """Validate PowerSource configuration file"""
    print_status("🔧 Validating PowerSource configuration...")
    
    if not config_path.exists():
        print_status(f"Configuration file missing: {config_path}", "ERROR")
        return False, {}
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check required structure
        required_keys = ['powersources', 'validation_settings', 'output_settings']
        for key in required_keys:
            if key not in config:
                print_status(f"Missing required config section: {key}", "ERROR")
                return False, {}
        
        # Validate PowerSources
        powersources = config.get('powersources', {})
        if not powersources:
            print_status("No PowerSources defined in configuration", "ERROR")
            return False, config
        
        print_status(f"Found {len(powersources)} PowerSources:")
        for gin, name in powersources.items():
            if validate_powersource_gin(gin):
                print_status(f"  ✅ {gin}: {name}")
            else:
                print_status(f"  ❌ Invalid GIN format: {gin}", "ERROR")
                return False, config
        
        print_status("✅ Configuration file is valid")
        return True, config
        
    except json.JSONDecodeError as e:
        print_status(f"Invalid JSON in configuration file: {e}", "ERROR")
        return False, {}
    except Exception as e:
        print_status(f"Error reading configuration file: {e}", "ERROR")
        return False, {}

def validate_source_files() -> bool:
    """Validate all required source files exist"""
    print_status("📁 Validating source files...")
    
    base_path = Path("Datasets")
    files_valid = True
    
    # Core source files
    core_files = [
        (base_path / "ENG.json", "Master product catalog"),
        (base_path / "golden_pkg_format_V2.xlsx", "Golden packages"),
        (base_path / "sales_data_cleaned.csv", "Sales data")
    ]
    
    for file_path, description in core_files:
        if not check_file_exists(file_path, description):
            files_valid = False
    
    # Check ruleset directory
    ruleset_dir = base_path / "Ruleset"
    if ruleset_dir.exists():
        excel_files = list(ruleset_dir.glob("*.xlsx")) + list(ruleset_dir.glob("*.xlsb"))
        print_status(f"✅ Ruleset directory contains {len(excel_files)} Excel files")
        for excel_file in excel_files:
            print_status(f"  📋 {excel_file.name}")
    else:
        print_status("❌ Ruleset directory missing", "ERROR")
        files_valid = False
    
    return files_valid

def validate_executables() -> bool:
    """Validate required Python scripts exist"""
    print_status("🔧 Validating execution scripts...")
    
    dt_path = Path("dt")
    scripts_valid = True
    
    required_scripts = [
        "powersource_orchestrator.py",
        "powersource_master_extractor.py", 
        "product_catalog_transformer.py"
    ]
    
    for script in required_scripts:
        script_path = dt_path / script
        if not check_file_exists(script_path, f"Execution script ({script})"):
            scripts_valid = False
    
    return scripts_valid

def validate_output_directory() -> bool:
    """Check output directory is accessible"""
    print_status("📂 Validating output directory...")
    
    output_dir = Path("neo4j_datasets")
    if not output_dir.exists():
        try:
            output_dir.mkdir(exist_ok=True)
            print_status(f"✅ Created output directory: {output_dir}")
        except Exception as e:
            print_status(f"❌ Cannot create output directory: {e}", "ERROR")
            return False
    else:
        print_status(f"✅ Output directory exists: {output_dir}")
    
    # Check write permissions
    try:
        test_file = output_dir / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        print_status("✅ Output directory is writable")
        return True
    except Exception as e:
        print_status(f"❌ Output directory not writable: {e}", "ERROR")
        return False

def check_sample_data(config: Dict) -> bool:
    """Check if sample data exists for configured PowerSources"""
    print_status("🔍 Checking sample data availability...")
    
    powersources = config.get('powersources', {})
    if not powersources:
        return True
    
    # Check golden packages
    try:
        golden_pkg_path = Path("Datasets/golden_pkg_format_V2.xlsx")
        if golden_pkg_path.exists():
            df = pd.read_excel(golden_pkg_path)
            found_powersources = set()
            
            for gin in powersources.keys():
                # Check different possible column formats
                for col in df.columns:
                    if 'gin' in col.lower() and 'power' in col.lower():
                        if gin in df[col].astype(str).str.zfill(10).values:
                            found_powersources.add(gin)
                            break
            
            print_status(f"Found {len(found_powersources)}/{len(powersources)} PowerSources in golden packages")
            
            missing_powersources = set(powersources.keys()) - found_powersources
            if missing_powersources:
                print_status(f"Missing PowerSources in golden packages: {missing_powersources}", "WARN")
            
    except Exception as e:
        print_status(f"Could not validate golden packages: {e}", "WARN")
    
    # Check ruleset files
    ruleset_dir = Path("Datasets/Ruleset")
    if ruleset_dir.exists():
        excel_files = [f.stem for f in ruleset_dir.glob("*.xlsx")] + [f.stem for f in ruleset_dir.glob("*.xlsb")]
        
        found_rulesets = 0
        for gin, name in powersources.items():
            # Try to match PowerSource name to ruleset filename
            name_parts = name.replace(" ", "").replace("-", "").replace(",", "").lower()
            for excel_file in excel_files:
                if any(part in excel_file.lower() for part in name_parts.split() if len(part) > 3):
                    found_rulesets += 1
                    break
        
        print_status(f"Found potential rulesets for {found_rulesets}/{len(powersources)} PowerSources")
    
    return True

def main():
    """Main validation function"""
    print_status("PowerSource System Validation", "HEADER")
    print_status("=" * 40, "HEADER")
    
    # Check if we're in the right directory
    if not Path("dt/powersource_orchestrator.py").exists():
        print_status("Please run this script from the AgenticAI/Recommender directory", "ERROR")
        sys.exit(1)
    
    validation_results = []
    
    # Validate configuration
    config_path = Path("powersource_config.json")
    config_valid, config = validate_config_file(config_path)
    validation_results.append(("Configuration", config_valid))
    
    # Validate source files
    files_valid = validate_source_files()
    validation_results.append(("Source Files", files_valid))
    
    # Validate executables
    scripts_valid = validate_executables()
    validation_results.append(("Execution Scripts", scripts_valid))
    
    # Validate output directory
    output_valid = validate_output_directory()
    validation_results.append(("Output Directory", output_valid))
    
    # Check sample data
    if config_valid:
        check_sample_data(config)
    
    # Summary
    print_status("=" * 40, "HEADER")
    print_status("Validation Summary:", "HEADER")
    
    all_valid = True
    for component, is_valid in validation_results:
        status = "✅ PASS" if is_valid else "❌ FAIL"
        print_status(f"{component}: {status}")
        if not is_valid:
            all_valid = False
    
    if all_valid:
        print_status("🎉 System validation successful! Ready for PowerSource extraction.", "HEADER")
        print_status("Run: ./run_powersource_extraction.sh to start processing")
        sys.exit(0)
    else:
        print_status("❌ System validation failed. Please address the issues above.", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()