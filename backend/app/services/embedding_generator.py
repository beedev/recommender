"""
Enhanced Product Embedding Generator for Neo4j Vector Storage

Generates semantic embeddings for welding products using comprehensive
specification extraction and HTML cleaning for improved search accuracy.
Enhanced with domain-specific vocabulary weighting for better product name matching.
"""

import json
import re
import logging
import yaml
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from bs4 import BeautifulSoup

import torch
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


@dataclass
class ProductEmbedding:
    """Product embedding data structure"""
    gin: str
    embedding: List[float]
    embedding_text: str
    embedding_model: str
    embedding_created_at: str


class ProductEmbeddingGenerator:
    """
    Enhanced Product Embedding Generator
    
    Generates 384-dimensional semantic embeddings for welding products
    using comprehensive specification extraction and HTML cleaning.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize with sentence transformer model.
        
        Args:
            model_name: HuggingFace model name for embeddings
        """
        self.model_name = model_name
        self.model = None
        self.domain_vocabulary = None
        self.load_model()
        self.load_domain_vocabulary()
        
        # Comprehensive specification field mappings for readability
        self.field_mappings = {
            # Process and application fields
            "process": "welding process",
            "processes": "welding processes",
            "application": "application",
            "applications": "applications",
            "industry": "industry",
            "use_case": "use case",
            "use_cases": "use cases",
            
            # Power and electrical specs
            "input_voltage": "input voltage",
            "output_voltage": "output voltage",
            "input_current": "input current",
            "output_current": "output current",
            "amperage": "amperage",
            "voltage": "voltage",
            "power": "power",
            "duty_cycle": "duty cycle",
            "electrical_requirements": "electrical requirements",
            
            # Physical specifications
            "dimensions": "dimensions",
            "weight": "weight",
            "size": "size",
            "portability": "portability",
            "mounting": "mounting",
            
            # Material and capability specs
            "material_thickness": "material thickness",
            "material_type": "material type",
            "wire_diameter": "wire diameter",
            "electrode_diameter": "electrode diameter",
            "feed_speed": "wire feed speed",
            "travel_speed": "travel speed",
            
            # Environmental and operational
            "environment": "environment",
            "operating_temperature": "operating temperature",
            "protection_rating": "protection rating",
            "certification": "certification",
            "compliance": "compliance",
            
            # Connectivity and control
            "connectivity": "connectivity",
            "control_type": "control type",
            "interface": "interface",
            "remote_control": "remote control",
            "automation": "automation"
        }
    
    def load_model(self) -> None:
        """Load the sentence transformer model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Model loaded successfully. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            raise
    
    def load_domain_vocabulary(self) -> None:
        """Load domain-specific vocabulary from config files with weights"""
        try:
            # Get paths to config files
            config_dir = os.path.join(os.path.dirname(__file__), '../../config')
            mode_detection_path = os.path.join(config_dir, 'mode_detection.yaml')
            welding_processes_path = os.path.join(config_dir, 'welding_processes.yaml')
            
            self.domain_vocabulary = {
                'product_names': {},      # weight: 3.0 - highest priority for exact matching
                'processes': {},          # weight: 2.5 - welding processes  
                'technical_terms': {},    # weight: 2.0 - technical specifications
                'materials': {},          # weight: 1.8 - material types
                'applications': {},       # weight: 1.5 - use cases and applications
                'general_terms': {}       # weight: 1.2 - general welding terms
            }
            
            # Load mode detection vocabulary
            if os.path.exists(mode_detection_path):
                with open(mode_detection_path, 'r') as f:
                    mode_config = yaml.safe_load(f)
                    
                # Extract product names from expert signals
                expert_signals = mode_config.get('expert_signals', [])
                for signal in expert_signals:
                    # Product names typically contain model numbers or specific brand names
                    if any(char.isdigit() for char in signal) or signal in ['Aristo 500 ix', 'Warrior 400i', 'Renegade 300']:
                        self.domain_vocabulary['product_names'][signal.lower()] = 3.0
                    elif signal.upper() in ['MIG', 'TIG', 'GMAW', 'GTAW', 'SMAW', 'FCAW']:
                        self.domain_vocabulary['processes'][signal.lower()] = 2.5
                    else:
                        self.domain_vocabulary['technical_terms'][signal.lower()] = 2.0
            
            # Load welding processes vocabulary        
            if os.path.exists(welding_processes_path):
                with open(welding_processes_path, 'r') as f:
                    welding_config = yaml.safe_load(f)
                    
                # Load welding processes
                processes = welding_config.get('welding_processes', {})
                if processes.get('primary'):
                    for process in processes['primary']:
                        self.domain_vocabulary['processes'][process.lower()] = 2.5
                if processes.get('technical'):
                    for process in processes['technical']:
                        self.domain_vocabulary['processes'][process.lower()] = 2.5
                        
                # Load materials
                materials = welding_config.get('materials', {})
                if materials.get('primary'):
                    for material in materials['primary']:
                        self.domain_vocabulary['materials'][material.lower().replace('_', ' ')] = 1.8
                        
                # Load applications
                applications = welding_config.get('applications', [])
                for app in applications:
                    self.domain_vocabulary['applications'][app.lower()] = 1.5
                    
                # Load industries (general terms)
                industries = welding_config.get('industries', [])
                for industry in industries:
                    self.domain_vocabulary['general_terms'][industry.lower()] = 1.2
            
            # Add common product name patterns for better matching
            common_product_patterns = [
                'renegade', 'warrior', 'aristo', 'robustfeed', 'cool2', 'cooling unit',
                'wire feeder', 'power source', 'torch', 'electrode holder'
            ]
            for pattern in common_product_patterns:
                self.domain_vocabulary['product_names'][pattern.lower()] = 3.0
                
            total_terms = sum(len(category) for category in self.domain_vocabulary.values())
            logger.info(f"Loaded domain vocabulary: {total_terms} terms across {len(self.domain_vocabulary)} categories")
            
        except Exception as e:
            logger.warning(f"Failed to load domain vocabulary: {e}")
            # Initialize empty vocabulary if loading fails
            self.domain_vocabulary = {'product_names': {}, 'processes': {}, 'technical_terms': {}, 'materials': {}, 'applications': {}, 'general_terms': {}}
    
    def _enhance_with_domain_vocabulary(self, text: str) -> str:
        """
        Enhance text by emphasizing domain-specific terms with repetition weighting.
        
        Args:
            text: Original text to enhance
            
        Returns:
            Enhanced text with domain-specific terms emphasized
        """
        if not text or not self.domain_vocabulary:
            return text
            
        enhanced_parts = [text]  # Start with original text
        
        # Normalize text for matching
        text_lower = text.lower()
        
        # Check each vocabulary category and apply weighting
        for category, terms in self.domain_vocabulary.items():
            for term, weight in terms.items():
                if term in text_lower:
                    # Calculate repetition count based on weight
                    # product_names (weight 3.0) -> repeat 2 times
                    # processes (weight 2.5) -> repeat 1-2 times  
                    # other terms -> repeat 1 time or add context
                    
                    if weight >= 3.0:  # Product names - highest priority
                        repetitions = 2
                        enhanced_parts.append(f"{term} {term}")
                    elif weight >= 2.5:  # Welding processes
                        repetitions = 1
                        enhanced_parts.append(f"{term} welding process")
                    elif weight >= 2.0:  # Technical terms
                        enhanced_parts.append(f"{term} specification")
                    elif weight >= 1.5:  # Materials and applications
                        enhanced_parts.append(f"{term} application")
        
        # Join all parts with spaces
        enhanced_text = ' '.join(enhanced_parts)
        
        # Clean up excessive spaces
        enhanced_text = re.sub(r'\s+', ' ', enhanced_text)
        
        return enhanced_text.strip()
    
    def _clean_html_description(self, description: str) -> str:
        """
        Clean HTML description and convert to readable text.
        
        Args:
            description: Raw HTML description
            
        Returns:
            Cleaned text description
        """
        if not description:
            return ""
        
        try:
            # Unescape HTML entities
            text = unescape(description)
            
            # Parse HTML and extract text
            soup = BeautifulSoup(text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Remove excessive punctuation and clean up
            text = re.sub(r'[^\w\s\-\.\,\(\)]', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            
            return text.strip()
            
        except Exception as e:
            logger.warning(f"Failed to clean HTML description: {e}")
            # Fallback: simple text cleaning
            text = re.sub(r'<[^>]+>', ' ', description)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
    
    def _humanize_field_name(self, field_name: str) -> str:
        """
        Convert field name to human-readable format.
        
        Args:
            field_name: Raw field name from specifications
            
        Returns:
            Human-readable field name
        """
        # Check if we have a specific mapping
        if field_name.lower() in self.field_mappings:
            return self.field_mappings[field_name.lower()]
        
        # Generic conversion: snake_case to readable
        readable = field_name.replace('_', ' ').replace('-', ' ')
        readable = re.sub(r'([a-z])([A-Z])', r'\1 \2', readable)
        return readable.lower().strip()
    
    def _clean_spec_value(self, value) -> str:
        """
        Clean and normalize specification value.
        
        Args:
            value: Specification value (any type)
            
        Returns:
            Cleaned string value
        """
        if value is None:
            return ""
        
        # Convert to string
        str_value = str(value).strip()
        
        if not str_value:
            return ""
        
        # Clean HTML if present
        if '<' in str_value and '>' in str_value:
            str_value = self._clean_html_description(str_value)
        
        # Normalize units and formatting
        str_value = re.sub(r'\s+', ' ', str_value)
        str_value = str_value.replace('&amp;', '&')
        
        return str_value.strip()
    
    def _extract_all_specifications(self, specs_json: str) -> str:
        """
        Extract ALL specifications comprehensively without hardcoding.
        
        Args:
            specs_json: JSON string containing product specifications
            
        Returns:
            Comprehensive specification text for embedding
        """
        if not specs_json:
            return ''
        
        try:
            specs = json.loads(specs_json)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse specifications JSON: {e}")
            return ''
        
        if not isinstance(specs, dict):
            return ''
        
        spec_texts = []
        
        # Extract all specification fields
        for field_name, field_values in specs.items():
            if not field_values:
                continue
            
            # Convert field name to readable text
            readable_field = self._humanize_field_name(field_name)
            
            # Handle different value types
            if isinstance(field_values, list):
                # Multiple values - extract all
                for value in field_values:
                    cleaned_value = self._clean_spec_value(value)
                    if cleaned_value:
                        spec_texts.append(f"{readable_field} {cleaned_value}")
            elif isinstance(field_values, dict):
                # Nested dictionary - flatten
                for sub_key, sub_value in field_values.items():
                    cleaned_value = self._clean_spec_value(sub_value)
                    if cleaned_value:
                        sub_field = self._humanize_field_name(sub_key)
                        spec_texts.append(f"{readable_field} {sub_field} {cleaned_value}")
            else:
                # Single value
                cleaned_value = self._clean_spec_value(field_values)
                if cleaned_value:
                    spec_texts.append(f"{readable_field} {cleaned_value}")
        
        return ' '.join(spec_texts)
    
    def _extract_name_components(self, name: str) -> str:
        """
        Extract meaningful components from product name.
        
        Args:
            name: Product name
            
        Returns:
            Processed name text
        """
        if not name:
            return ""
        
        # Split name into components and filter meaningful parts
        components = re.split(r'[\s\-_/]+', name)
        
        # Filter out very short or purely numeric components
        meaningful_components = []
        for comp in components:
            comp = comp.strip()
            if len(comp) >= 2 and not comp.isdigit():
                meaningful_components.append(comp)
        
        return ' '.join(meaningful_components)
    
    def generate_embedding_text(self, product: Dict) -> str:
        """
        Generate comprehensive embedding text for a product.
        
        Args:
            product: Product data dictionary
            
        Returns:
            Complete text for embedding generation
        """
        text_parts = []
        
        # 1. Product name (processed)
        name = product.get('name') or ''
        if isinstance(name, str) and name.strip():
            name_components = self._extract_name_components(name.strip())
            text_parts.append(name_components)
        
        # 2. Category and subcategory
        category = product.get('category') or ''
        if isinstance(category, str) and category.strip():
            text_parts.append(f"category {category.strip()}")
        
        subcategory = product.get('subcategory') or ''
        if isinstance(subcategory, str) and subcategory.strip() and subcategory.strip() != category:
            text_parts.append(f"subcategory {subcategory.strip()}")
        
        # 3. Comprehensive specifications (ALL fields)
        specs_json = product.get('specifications_json', '')
        if specs_json:
            spec_text = self._extract_all_specifications(specs_json)
            if spec_text:
                text_parts.append(spec_text)
        
        # 4. Cleaned description
        description = product.get('description') or ''
        if isinstance(description, str) and description.strip():
            cleaned_desc = self._clean_html_description(description)
            if cleaned_desc:
                # Truncate very long descriptions to avoid token limits
                if len(cleaned_desc) > 500:
                    cleaned_desc = cleaned_desc[:500] + "..."
                text_parts.append(cleaned_desc)
        
        # Join all parts
        complete_text = ' '.join(text_parts)
        
        # Enhance with domain-specific vocabulary weighting
        enhanced_text = self._enhance_with_domain_vocabulary(complete_text)
        
        # Final cleanup
        enhanced_text = re.sub(r'\s+', ' ', enhanced_text)
        enhanced_text = enhanced_text.strip()
        
        logger.debug(f"Generated enhanced embedding text for {product.get('gin', 'unknown')}: {len(enhanced_text)} characters (original: {len(complete_text)})")
        
        return enhanced_text
    
    def generate_embedding(self, product: Dict) -> Optional[ProductEmbedding]:
        """
        Generate embedding for a single product.
        
        Args:
            product: Product data dictionary
            
        Returns:
            ProductEmbedding object or None if generation fails
        """
        try:
            # Generate comprehensive embedding text
            embedding_text = self.generate_embedding_text(product)
            
            if not embedding_text:
                logger.warning(f"No embedding text generated for product {product.get('gin', 'unknown')}")
                return None
            
            # Generate embedding vector
            embedding_vector = self.model.encode(embedding_text)
            
            # Convert to list of floats
            embedding_list = embedding_vector.tolist()
            
            # Create ProductEmbedding object
            product_embedding = ProductEmbedding(
                gin=product.get('gin', ''),
                embedding=embedding_list,
                embedding_text=embedding_text,
                embedding_model=self.model_name,
                embedding_created_at=datetime.utcnow().isoformat() + 'Z'
            )
            
            logger.debug(f"Generated embedding for {product_embedding.gin}: {len(embedding_list)} dimensions")
            
            return product_embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding for product {product.get('gin', 'unknown')}: {e}")
            return None
    
    def generate_embeddings_batch(self, products: List[Dict]) -> List[ProductEmbedding]:
        """
        Generate embeddings for multiple products efficiently.
        
        Args:
            products: List of product data dictionaries
            
        Returns:
            List of ProductEmbedding objects
        """
        embeddings = []
        successful = 0
        failed = 0
        
        logger.info(f"Generating embeddings for {len(products)} products")
        
        for i, product in enumerate(products):
            if i % 10 == 0:
                logger.info(f"Processing product {i+1}/{len(products)}")
            
            embedding = self.generate_embedding(product)
            if embedding:
                embeddings.append(embedding)
                successful += 1
            else:
                failed += 1
        
        logger.info(f"Embedding generation complete: {successful} successful, {failed} failed")
        
        return embeddings
    
    def query_embedding(self, query_text: str) -> List[float]:
        """
        Generate embedding for a search query with domain vocabulary enhancement.
        
        Args:
            query_text: Search query text
            
        Returns:
            Query embedding vector
        """
        try:
            # Clean and normalize query text
            cleaned_query = re.sub(r'\s+', ' ', query_text.strip())
            
            # Enhance query with domain-specific vocabulary weighting
            enhanced_query = self._enhance_with_domain_vocabulary(cleaned_query)
            
            logger.debug(f"Enhanced query: '{cleaned_query}' -> '{enhanced_query}'")
            
            # Generate embedding
            embedding_vector = self.model.encode(enhanced_query)
            
            return embedding_vector.tolist()
            
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise