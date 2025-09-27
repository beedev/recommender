# New Trinity generation logic to replace lines 834-866 in sales_loader.py

def _create_trinity_relationships_fixed(self, orders: Dict[str, List[SalesRecord]]):
    """
    Create FORMS_TRINITY relationships with multi-PowerSource compatibility logic.
    
    For each PowerSource in an order:
    1. Find compatible feeder from order components using DETERMINES relationships
    2. Find compatible cooler from order components using DETERMINES relationships  
    3. Only create Trinity if compatible components found (exception: Renegade uses F-GINs)
    4. Remove PowerSources without compatible components from Trinity formation
    """
    if not orders:
        return
        
    self.logger.info("Creating Trinity relationships with multi-PowerSource compatibility...")
    
    # Load DETERMINES relationships for compatibility checking
    determines_relationships = self._load_determines_relationships()
    
    trinity_combinations = []
    trinity_count = 0
    skipped_powersources = []
    
    for order_id, records in orders.items():
        # Group products by category for this order
        products_by_category = {}
        for record in records:
            category = getattr(record, 'category', '')
            if category in ['PowerSource', 'Feeder', 'Cooler']:
                if category not in products_by_category:
                    products_by_category[category] = []
                products_by_category[category].append(record.gin)
        
        # Skip orders without PowerSources
        if 'PowerSource' not in products_by_category:
            continue
            
        powersources = products_by_category.get('PowerSource', [])
        feeders = products_by_category.get('Feeder', [])
        coolers = products_by_category.get('Cooler', [])
        
        # Create Trinity for each PowerSource in the order
        for ps_gin in powersources:
            
            # Find compatible feeder for this PowerSource
            compatible_feeder = self._find_compatible_component(
                ps_gin, feeders, 'Feeder', determines_relationships
            )
            
            # Find compatible cooler for this PowerSource  
            compatible_cooler = self._find_compatible_component(
                ps_gin, coolers, 'Cooler', determines_relationships
            )
            
            # Check if Trinity can be formed
            if compatible_feeder and compatible_cooler:
                trinity_id = f"{ps_gin}_{compatible_feeder}_{compatible_cooler}"
                
                trinity_combinations.append({
                    'order_id': order_id,
                    'powersource_gin': ps_gin,
                    'feeder_gin': compatible_feeder,
                    'cooler_gin': compatible_cooler,
                    'trinity_id': trinity_id
                })
                trinity_count += 1
                
            else:
                # Log skipped PowerSources for analysis
                skipped_powersources.append({
                    'order_id': order_id,
                    'powersource_gin': ps_gin,
                    'missing_feeder': compatible_feeder is None,
                    'missing_cooler': compatible_cooler is None,
                    'available_feeders': feeders,
                    'available_coolers': coolers
                })
    
    self.logger.info(f"Found {trinity_count} Trinity combinations from {len(orders)} orders")
    self.logger.info(f"Skipped {len(skipped_powersources)} PowerSources without compatible components")
    
    # Log details of skipped PowerSources for debugging
    for skipped in skipped_powersources[:5]:  # Show first 5 for debugging
        self.logger.warning(
            f"Skipped PowerSource {skipped['powersource_gin']} in order {skipped['order_id']}: "
            f"Missing feeder={skipped['missing_feeder']}, Missing cooler={skipped['missing_cooler']}"
        )
    
    if not trinity_combinations:
        self.logger.warning("No Trinity combinations found - skipping Trinity relationship creation")
        return
        
    # Continue with existing Trinity creation logic...
    # (Rest of the method remains the same from line 870 onwards)


def _load_determines_relationships(self):
    """Load DETERMINES relationships from database for compatibility checking"""
    try:
        with self.neo4j_driver.session(database=self.neo4j_database) as session:
            query = """
            MATCH (ps:Product)-[d:DETERMINES]->(comp:Product)
            WHERE ps.category = 'PowerSource'
            RETURN ps.gin as powersource_gin, 
                   comp.gin as component_gin,
                   comp.category as component_category
            """
            results = session.run(query).data()
            
            # Group by powersource -> category -> [components]
            determines_map = {}
            for record in results:
                ps_gin = record['powersource_gin'] 
                comp_gin = record['component_gin']
                comp_category = record['component_category']
                
                if ps_gin not in determines_map:
                    determines_map[ps_gin] = {}
                if comp_category not in determines_map[ps_gin]:
                    determines_map[ps_gin][comp_category] = []
                    
                determines_map[ps_gin][comp_category].append(comp_gin)
            
            self.logger.info(f"Loaded DETERMINES relationships for {len(determines_map)} PowerSources")
            return determines_map
            
    except Exception as e:
        self.logger.error(f"Failed to load DETERMINES relationships: {e}")
        return {}


def _find_compatible_component(self, powersource_gin, available_components, component_category, determines_relationships):
    """
    Find compatible component for PowerSource from available components in the order.
    
    Args:
        powersource_gin: PowerSource GIN to find compatible component for
        available_components: List of component GINs available in the order
        component_category: 'Feeder' or 'Cooler' 
        determines_relationships: Loaded DETERMINES relationships
        
    Returns:
        Compatible component GIN or None if no compatible component found
    """
    # Get components that this PowerSource DETERMINES
    ps_determines = determines_relationships.get(powersource_gin, {})
    required_components = ps_determines.get(component_category, [])
    
    # Find intersection between required and available
    compatible_components = [comp for comp in available_components if comp in required_components]
    
    if compatible_components:
        # Return first compatible component (could be enhanced with priority logic)
        return compatible_components[0]
    
    # No compatible component found
    return None
