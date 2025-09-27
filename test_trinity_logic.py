#!/usr/bin/env python3
"""
Test the new Trinity generation logic with Order 100640282
"""

# Simulate the problematic order data
order_100640282 = {
    'PowerSource': ['0446200880', '0445250880'],  # Aristo 500ix, Renegade ES 300i
    'Feeder': ['0445800898', 'F000000007'],       # RobustFeed U82, No Feeder Available  
    'Cooler': ['0465427880', 'F000000005']        # COOL 2, No Cooler Available
}

# Simulate DETERMINES relationships (from our earlier database query)
determines_relationships = {
    '0446200880': {  # Aristo 500ix DETERMINES
        'Feeder': ['0445800898'],     # RobustFeed U82 (real feeder)
        'Cooler': ['0465427880']      # COOL 2 (real cooler)
    },
    '0445250880': {  # Renegade ES 300i DETERMINES  
        'Feeder': ['F000000007'],     # No Feeder Available
        'Cooler': ['F000000005']      # No Cooler Available
    }
}

def find_compatible_component(powersource_gin, available_components, component_category, determines_relationships):
    """Test implementation of compatibility logic"""
    # Get components that this PowerSource DETERMINES
    ps_determines = determines_relationships.get(powersource_gin, {})
    required_components = ps_determines.get(component_category, [])
    
    # Find intersection between required and available
    compatible_components = [comp for comp in available_components if comp in required_components]
    
    if compatible_components:
        return compatible_components[0]
    return None

def test_trinity_generation():
    """Test Trinity generation for Order 100640282"""
    print("🧪 Testing new Trinity generation logic")
    print("=" * 60)
    
    powersources = order_100640282['PowerSource']
    feeders = order_100640282['Feeder'] 
    coolers = order_100640282['Cooler']
    
    print(f"Order 100640282 components:")
    print(f"  PowerSources: {powersources}")
    print(f"  Feeders: {feeders}")
    print(f"  Coolers: {coolers}")
    print()
    
    trinity_combinations = []
    
    for ps_gin in powersources:
        print(f"🔍 Processing PowerSource: {ps_gin}")
        
        # Find compatible feeder
        compatible_feeder = find_compatible_component(
            ps_gin, feeders, 'Feeder', determines_relationships
        )
        
        # Find compatible cooler
        compatible_cooler = find_compatible_component(
            ps_gin, coolers, 'Cooler', determines_relationships
        )
        
        print(f"  Compatible Feeder: {compatible_feeder}")
        print(f"  Compatible Cooler: {compatible_cooler}")
        
        if compatible_feeder and compatible_cooler:
            trinity_id = f"{ps_gin}_{compatible_feeder}_{compatible_cooler}"
            trinity = {
                'powersource_gin': ps_gin,
                'feeder_gin': compatible_feeder, 
                'cooler_gin': compatible_cooler,
                'trinity_id': trinity_id
            }
            trinity_combinations.append(trinity)
            print(f"  ✅ Trinity Created: {trinity_id}")
        else:
            print(f"  ❌ Trinity Skipped: Missing compatible components")
        
        print()
    
    print("🎯 Final Trinity Combinations:")
    for i, trinity in enumerate(trinity_combinations, 1):
        print(f"  {i}. {trinity['trinity_id']}")
        print(f"     PowerSource: {trinity['powersource_gin']}")
        print(f"     Feeder: {trinity['feeder_gin']}")
        print(f"     Cooler: {trinity['cooler_gin']}")
        print()
    
    print(f"📊 Results: {len(trinity_combinations)} Trinity combinations created")
    
    return trinity_combinations

if __name__ == "__main__":
    trinity_combinations = test_trinity_generation()