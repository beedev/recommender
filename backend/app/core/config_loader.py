"""
Configuration Loader for Welding Domain Knowledge
Centralized loading of welding processes, materials, and validation rules from YAML files
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum
from functools import lru_cache

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Load and manage domain configuration from YAML files"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            # Default to config directory relative to this file
            self.config_dir = Path(__file__).parent.parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)
        
        self._welding_config = None
        self._mode_config = None
    
    @lru_cache(maxsize=1)
    def load_welding_config(self) -> Dict[str, Any]:
        """Load welding processes configuration with caching"""
        if self._welding_config is None:
            config_file = self.config_dir / "welding_processes.yaml"
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self._welding_config = yaml.safe_load(f)
                logger.info(f"Loaded welding configuration from {config_file}")
            except FileNotFoundError:
                logger.error(f"Welding config file not found: {config_file}")
                self._welding_config = self._get_default_welding_config()
            except yaml.YAMLError as e:
                logger.error(f"Error parsing welding config: {e}")
                self._welding_config = self._get_default_welding_config()
        
        return self._welding_config
    
    @lru_cache(maxsize=1)
    def load_mode_detection_config(self) -> Dict[str, Any]:
        """Load mode detection configuration with caching"""
        if self._mode_config is None:
            config_file = self.config_dir / "mode_detection.yaml"
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self._mode_config = yaml.safe_load(f)
                logger.info(f"Loaded mode detection configuration from {config_file}")
            except FileNotFoundError:
                logger.error(f"Mode detection config file not found: {config_file}")
                self._mode_config = {}
            except yaml.YAMLError as e:
                logger.error(f"Error parsing mode detection config: {e}")
                self._mode_config = {}
        
        return self._mode_config
    
    def get_all_welding_processes(self) -> List[str]:
        """Get all supported welding processes (primary + technical)"""
        config = self.load_welding_config()
        processes = []
        
        if 'welding_processes' in config:
            processes.extend(config['welding_processes'].get('primary', []))
            processes.extend(config['welding_processes'].get('technical', []))
        
        return list(set(processes))  # Remove duplicates
    
    def get_primary_welding_processes(self) -> List[str]:
        """Get primary welding process names for enum generation"""
        config = self.load_welding_config()
        return config.get('welding_processes', {}).get('primary', [])
    
    def get_technical_welding_processes(self) -> List[str]:
        """Get technical welding process acronyms"""
        config = self.load_welding_config()
        return config.get('welding_processes', {}).get('technical', [])
    
    def get_materials(self) -> List[str]:
        """Get all supported materials"""
        config = self.load_welding_config()
        return config.get('materials', {}).get('primary', [])
    
    def get_industries(self) -> List[str]:
        """Get all supported industries"""
        config = self.load_welding_config()
        return config.get('industries', [])
    
    def get_process_aliases(self, process: str) -> List[str]:
        """Get aliases for a welding process"""
        config = self.load_welding_config()
        aliases = config.get('welding_processes', {}).get('aliases', {})
        return aliases.get(process, [])
    
    def normalize_process_name(self, process_input: str) -> Optional[str]:
        """Normalize process input to primary process name"""
        config = self.load_welding_config()
        
        # Check if it's already a primary process
        primary_processes = self.get_primary_welding_processes()
        if process_input.upper() in [p.upper() for p in primary_processes]:
            return process_input.upper()
        
        # Check technical acronyms
        technical_processes = self.get_technical_welding_processes()
        if process_input.upper() in [p.upper() for p in technical_processes]:
            # Map technical to primary
            mapping = {
                'GMAW': 'MIG',
                'GTAW': 'TIG',
                'SMAW': 'STICK',
                'FCAW': 'FLUX_CORE'
            }
            return mapping.get(process_input.upper(), process_input.upper())
        
        # Check aliases
        aliases = config.get('welding_processes', {}).get('aliases', {})
        for primary, alias_list in aliases.items():
            if process_input.lower() in [a.lower() for a in alias_list]:
                return primary.upper()
        
        return None
    
    def _get_default_welding_config(self) -> Dict[str, Any]:
        """Fallback configuration if file loading fails"""
        return {
            'welding_processes': {
                'primary': ['MIG', 'TIG', 'STICK', 'MMA', 'FLUX_CORE', 'MULTI_PROCESS'],
                'technical': ['GMAW', 'GTAW', 'SMAW', 'FCAW']
            },
            'materials': {
                'primary': ['steel', 'stainless_steel', 'aluminum', 'carbon_steel']
            },
            'industries': ['automotive', 'aerospace', 'marine', 'construction', 'manufacturing', 'fabrication']
        }

# Global instance
config_loader = ConfigLoader()

def get_config_loader() -> ConfigLoader:
    """Get the global configuration loader instance"""
    return config_loader