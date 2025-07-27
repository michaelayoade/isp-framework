#!/usr/bin/env python3
"""
API Endpoint Inventory Script
Scans all FastAPI routers and extracts:
1. Router-level prefixes from include_router calls
2. Individual route decorators (@router.<method>)
3. Generates CSV inventory for consolidation analysis
"""

import os
import re
import csv
from pathlib import Path
from typing import List, Dict, Tuple

def extract_router_prefixes(api_file_path: str) -> List[Dict[str, str]]:
    """Extract router prefixes from api.py include_router calls"""
    prefixes = []
    
    try:
        with open(api_file_path, 'r') as f:
            content = f.read()
            
        # Pattern: api_router.include_router(module.router, prefix="/path", tags=["tag"])
        pattern = r'api_router\.include_router\([^,]+\.router,\s*prefix=["\']([^"\']+)["\']'
        matches = re.findall(pattern, content)
        
        for match in matches:
            prefixes.append({
                'type': 'router_prefix',
                'path': match,
                'file': api_file_path,
                'line': 'N/A'
            })
    except Exception as e:
        print(f"Error reading {api_file_path}: {e}")
    
    return prefixes

def extract_route_decorators(endpoint_file: str) -> List[Dict[str, str]]:
    """Extract individual route decorators from endpoint files"""
    routes = []
    
    try:
        with open(endpoint_file, 'r') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Pattern: @router.get("/path"), @router.post("/path"), etc.
            pattern = r'@router\.(get|post|put|patch|delete|options|head)\(["\']([^"\']+)["\']'
            match = re.search(pattern, line)
            
            if match:
                method, path = match.groups()
                routes.append({
                    'type': 'route_decorator',
                    'method': method.upper(),
                    'path': path,
                    'file': endpoint_file,
                    'line': str(line_num)
                })
    except Exception as e:
        print(f"Error reading {endpoint_file}: {e}")
    
    return routes

def combine_paths(router_prefix: str, route_path: str) -> str:
    """Combine router prefix with route path to get full API path"""
    # Remove leading/trailing slashes and combine
    prefix = router_prefix.strip('/')
    path = route_path.strip('/')
    
    if path:
        return f"/api/v1/{prefix}/{path}"
    else:
        return f"/api/v1/{prefix}"

def analyze_endpoint_files(endpoints_dir: str) -> List[Dict[str, str]]:
    """Analyze all endpoint files for route decorators"""
    all_routes = []
    
    endpoint_files = list(Path(endpoints_dir).glob("*.py"))
    print(f"Found {len(endpoint_files)} endpoint files")
    
    for endpoint_file in endpoint_files:
        if endpoint_file.name == "__init__.py":
            continue
            
        print(f"Analyzing: {endpoint_file.name}")
        routes = extract_route_decorators(str(endpoint_file))
        all_routes.extend(routes)
    
    return all_routes

def map_routes_to_prefixes(api_file: str, endpoints_dir: str) -> List[Dict[str, str]]:
    """Map route decorators to their router prefixes"""
    # Extract router prefixes from api.py
    prefixes = extract_router_prefixes(api_file)
    
    # Extract all route decorators
    routes = analyze_endpoint_files(endpoints_dir)
    
    # Create mapping of endpoint file to router prefix
    # This requires manual mapping based on import structure
    file_to_prefix = {
        'auth.py': '/auth',
        'portal_auth.py': '/auth/portal',
        'two_factor.py': '/auth/2fa',
        'oauth.py': '/auth/oauth',
        'reseller_auth.py': '/auth/reseller',
        'customers.py': '/customers',
        'customer_portal.py': '/customers',
        'services.py': '/services',
        'service_plans.py': '/services/plans',
        'service_templates.py': '/services/templates',
        'service_instances.py': '/services/instances',
        'service_provisioning.py': '/services/provisioning',
        'customer_services.py': '/customers/services',
        'billing.py': '/billing',
        'ticketing.py': '/tickets',
        'reseller.py': '/partners',
        'device_management.py': '/network/devices',
        'radius.py': '/network/radius',
        'alerts.py': '/alerts',
        'operational_dashboard.py': '/dashboard',
        'audit_management.py': '/audit',
        'api_management.py': '/api-management',
        'files.py': '/files',
        'communications.py': '/communications',
        'webhooks.py': '/webhooks',
        'dead_letter_queue.py': '/background',
    }
    
    # Combine routes with their prefixes
    combined_routes = []
    
    for route in routes:
        filename = Path(route['file']).name
        router_prefix = file_to_prefix.get(filename, '/unknown')
        
        full_path = combine_paths(router_prefix, route['path'])
        
        combined_routes.append({
            'current_path': full_path,
            'method': route.get('method', ''),
            'router_prefix': router_prefix,
            'route_path': route['path'],
            'file': route['file'],
            'line': route['line']
        })
    
    return combined_routes

def generate_csv_inventory(routes: List[Dict[str, str]], output_file: str):
    """Generate CSV inventory file"""
    
    # Sort routes by path for easier analysis
    routes.sort(key=lambda x: x['current_path'])
    
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['current_path', 'method', 'router_prefix', 'route_path', 'file', 'line']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for route in routes:
            writer.writerow(route)
    
    print(f"Generated inventory: {output_file}")
    print(f"Total routes: {len(routes)}")

def main():
    # Paths
    project_root = "/home/ispframework/projects/isp-framework"
    api_file = f"{project_root}/backend/app/api/v1/api.py"
    endpoints_dir = f"{project_root}/backend/app/api/v1/endpoints"
    output_file = f"{project_root}/docs/API_PATH_INVENTORY.csv"
    
    # Ensure docs directory exists
    os.makedirs(f"{project_root}/docs", exist_ok=True)
    
    print("=== API Endpoint Inventory (Phase 1) ===")
    print(f"API file: {api_file}")
    print(f"Endpoints dir: {endpoints_dir}")
    print(f"Output: {output_file}")
    print()
    
    # Generate inventory
    routes = map_routes_to_prefixes(api_file, endpoints_dir)
    generate_csv_inventory(routes, output_file)
    
    # Summary statistics
    methods = {}
    prefixes = {}
    
    for route in routes:
        method = route.get('method', 'UNKNOWN')
        prefix = route.get('router_prefix', 'UNKNOWN')
        
        methods[method] = methods.get(method, 0) + 1
        prefixes[prefix] = prefixes.get(prefix, 0) + 1
    
    print("\n=== Summary Statistics ===")
    print(f"HTTP Methods:")
    for method, count in sorted(methods.items()):
        print(f"  {method}: {count}")
    
    print(f"\nRouter Prefixes:")
    for prefix, count in sorted(prefixes.items()):
        print(f"  {prefix}: {count}")
    
    print(f"\nInventory complete! Review {output_file} for full details.")

if __name__ == "__main__":
    main()
