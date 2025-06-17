#!/usr/bin/env python3
"""
Deployment Checklist Script
Validates that all submission requirements are met
"""

import os
import sys
import json
import requests
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'

def print_status(message, status):
    if status:
        print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")
    else:
        print(f"{Colors.RED}❌ {message}{Colors.ENDC}")
    return status

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.ENDC}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.ENDC}")

def check_files():
    """Check if all required files exist"""
    print(f"\n{Colors.BLUE}📁 Checking Code Repository Files{Colors.ENDC}")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'README.md',
        '.gitignore',
        'database_schema.sql',
        'setup.py',
        'DEPLOYMENT.md',
        'Expense_Splitter_API.postman_collection.json'
    ]
    
    all_files_exist = True
    for file in required_files:
        exists = os.path.exists(file)
        print_status(f"File exists: {file}", exists)
        if not exists:
            all_files_exist = False
    
    return all_files_exist

def check_git_setup():
    """Check git repository setup"""
    print(f"\n{Colors.BLUE}📚 Checking Git Repository Setup{Colors.ENDC}")
    
    git_init = os.path.exists('.git')
    print_status("Git repository initialized", git_init)
    
    if git_init:
        # Check if there are commits
        try:
            import subprocess
            result = subprocess.run(['git', 'log', '--oneline'], 
                                  capture_output=True, text=True)
            has_commits = len(result.stdout.strip()) > 0
            print_status("Has git commits", has_commits)
            
            # Check if remote is set
            result = subprocess.run(['git', 'remote', '-v'], 
                                  capture_output=True, text=True)
            has_remote = len(result.stdout.strip()) > 0
            print_status("Remote repository configured", has_remote)
            
            if has_remote:
                print_info(f"Remote: {result.stdout.strip().split()[1]}")
            
            return has_commits and has_remote
        except:
            print_warning("Could not check git status")
            return False
    
    return False

def test_local_api(base_url="http://localhost:5000"):
    """Test local API endpoints"""
    print(f"\n{Colors.BLUE}🔧 Testing Local API{Colors.ENDC}")
    
    endpoints = [
        ('GET', '/expenses', 'List expenses'),
        ('GET', '/people', 'List people'),
        ('GET', '/balances', 'Get balances'),
        ('GET', '/settlements', 'Get settlements'),
        ('GET', '/categories', 'Get categories'),
        ('GET', '/recurring', 'List recurring transactions'),
        ('GET', '/', 'Web dashboard')
    ]
    
    all_working = True
    
    for method, endpoint, description in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=5)
            
            if endpoint == '/':
                # Web dashboard should return HTML
                success = response.status_code == 200 and 'html' in response.headers.get('content-type', '').lower()
            else:
                # API endpoints should return JSON
                success = response.status_code == 200
                if success and 'application/json' in response.headers.get('content-type', ''):
                    data = response.json()
                    success = data.get('success', False)
            
            print_status(f"{method} {endpoint} - {description}", success)
            if not success:
                all_working = False
                
        except requests.exceptions.ConnectionError:
            print_status(f"{method} {endpoint} - {description}", False)
            print_warning("Could not connect to local server. Is it running?")
            all_working = False
        except Exception as e:
            print_status(f"{method} {endpoint} - {description}", False)
            print_warning(f"Error: {str(e)}")
            all_working = False
    
    return all_working

def test_deployed_api(base_url):
    """Test deployed API endpoints"""
    print(f"\n{Colors.BLUE}🌐 Testing Deployed API: {base_url}{Colors.ENDC}")
    
    endpoints = [
        ('GET', '/expenses', 'List expenses'),
        ('GET', '/people', 'List people'),
        ('GET', '/balances', 'Get balances'),
        ('GET', '/settlements', 'Get settlements'),
        ('GET', '/categories', 'Get categories'),
        ('GET', '/', 'Web dashboard')
    ]
    
    all_working = True
    
    for method, endpoint, description in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=10)
            
            if endpoint == '/':
                success = response.status_code == 200
            else:
                success = response.status_code == 200
                if success and 'application/json' in response.headers.get('content-type', ''):
                    data = response.json()
                    success = data.get('success', False)
            
            print_status(f"{method} {endpoint} - {description}", success)
            if not success:
                all_working = False
                print_warning(f"Status: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print_status(f"{method} {endpoint} - {description}", False)
            print_warning("Could not connect to deployed server")
            all_working = False
        except Exception as e:
            print_status(f"{method} {endpoint} - {description}", False)
            print_warning(f"Error: {str(e)}")
            all_working = False
    
    return all_working

def test_custom_splits():
    """Test the core requirement: custom splits functionality"""
    print(f"\n{Colors.BLUE}🧮 Testing Custom Splits (Core Requirement){Colors.ENDC}")
    
    try:
        # Test with local server
        base_url = "http://localhost:5000"
        
        # Test custom split expense
        custom_split_data = {
            "amount": 1000.00,
            "description": "Test Custom Split",
            "paid_by": "TestUser",
            "category": "Food",
            "splits": [
                {"person_name": "Person1", "split_type": "percentage", "split_value": 40},
                {"person_name": "Person2", "split_type": "exact", "split_value": 300},
                {"person_name": "Person3", "split_type": "equal"},
                {"person_name": "Person4", "split_type": "equal"}
            ]
        }
        
        response = requests.post(f"{base_url}/expenses", 
                               json=custom_split_data, 
                               timeout=5)
        
        if response.status_code == 201:
            data = response.json()
            success = data.get('success', False)
            
            if success and 'splits' in data.get('data', {}):
                splits = data['data']['splits']
                print_status("Custom splits functionality working", True)
                print_info(f"Created expense with {len(splits)} splits")
                
                # Verify split calculations
                total_calculated = sum(split['calculated_amount'] for split in splits)
                expected_total = custom_split_data['amount']
                
                calculation_correct = abs(total_calculated - expected_total) < 0.01
                print_status("Split calculations are correct", calculation_correct)
                
                return success and calculation_correct
            else:
                print_status("Custom splits functionality working", False)
                print_warning("Response missing splits data")
                return False
        else:
            print_status("Custom splits functionality working", False)
            print_warning(f"HTTP {response.status_code}: {response.text[:100]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_status("Custom splits functionality working", False)
        print_warning("Could not connect to local server for testing")
        return False
    except Exception as e:
        print_status("Custom splits functionality working", False)
        print_warning(f"Error testing custom splits: {str(e)}")
        return False

def validate_postman_collection():
    """Validate Postman collection file"""
    print(f"\n{Colors.BLUE}📮 Validating Postman Collection{Colors.ENDC}")
    
    try:
        with open('Expense_Splitter_API.postman_collection.json', 'r') as f:
            collection = json.load(f)
        
        # Check basic structure
        has_info = 'info' in collection
        print_status("Collection has info section", has_info)
        
        has_items = 'item' in collection and len(collection['item']) > 0
        print_status("Collection has request items", has_items)
        
        # Count requests
        total_requests = 0
        folders = collection.get('item', [])
        
        for folder in folders:
            if 'item' in folder:
                total_requests += len(folder['item'])
        
        print_info(f"Total API requests in collection: {total_requests}")
        
        # Check for required folders
        folder_names = [item.get('name', '') for item in folders]
        required_folders = [
            'Expense Management',
            'Recurring Transactions', 
            'Settlements & People',
            'Analytics & Categories',
            'Error Handling & Validation'
        ]
        
        all_folders_present = True
        for folder in required_folders:
            present = any(folder in name for name in folder_names)
            print_status(f"Has {folder} folder", present)
            if not present:
                all_folders_present = False
        
        # Check for base_url variable
        has_base_url = 'variable' in collection and any(
            var.get('key') == 'base_url' for var in collection['variable']
        )
        print_status("Has base_url variable", has_base_url)
        
        return has_info and has_items and all_folders_present and has_base_url and total_requests > 20
        
    except FileNotFoundError:
        print_status("Postman collection file exists", False)
        return False
    except json.JSONDecodeError:
        print_status("Postman collection is valid JSON", False)
        return False
    except Exception as e:
        print_status("Postman collection validation", False)
        print_warning(f"Error: {str(e)}")
        return False

def check_documentation():
    """Check documentation completeness"""
    print(f"\n{Colors.BLUE}📖 Checking Documentation{Colors.ENDC}")
    
    try:
        with open('README.md', 'r') as f:
            readme_content = f.read()
        
        required_sections = [
            'Features',
            'API Endpoints', 
            'Local Development Setup',
            'Settlement Calculation Logic',
            'Known Limitations',
            'Custom Split',
            'Postman Collection'
        ]
        
        all_sections_present = True
        for section in required_sections:
            present = section.lower() in readme_content.lower()
            print_status(f"README contains {section} section", present)
            if not present:
                all_sections_present = False
        
        # Check length (should be comprehensive)
        word_count = len(readme_content.split())
        adequate_length = word_count > 1500
        print_status(f"README is comprehensive ({word_count} words)", adequate_length)
        
        return all_sections_present and adequate_length
        
    except FileNotFoundError:
        print_status("README.md exists", False)
        return False

def generate_submission_report():
    """Generate final submission report"""
    print(f"\n{Colors.BLUE}📊 SUBMISSION CHECKLIST SUMMARY{Colors.ENDC}")
    print("=" * 50)
    
    checklist = [
        ("Code Repository", check_files()),
        ("Git Setup", check_git_setup()),
        ("Documentation", check_documentation()),
        ("Postman Collection", validate_postman_collection()),
        ("Custom Splits (Core Req)", test_custom_splits()),
        ("Local API", test_local_api())
    ]
    
    passed = sum(1 for _, status in checklist if status)
    total = len(checklist)
    
    print(f"\n{Colors.BLUE}Results: {passed}/{total} checks passed{Colors.ENDC}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}🎉 ALL CHECKS PASSED!{Colors.ENDC}")
        print(f"{Colors.GREEN}Your submission is ready for deployment!{Colors.ENDC}")
    else:
        print(f"\n{Colors.YELLOW}⚠️  Please fix the failing checks before submission{Colors.ENDC}")
    
    return passed == total

def main():
    """Main function"""
    print(f"{Colors.BLUE}🚀 Expense Splitter Deployment Checklist{Colors.ENDC}")
    print(f"{Colors.BLUE}Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
    print("=" * 60)
    
    # Run all checks
    all_passed = generate_submission_report()
    
    print(f"\n{Colors.BLUE}📋 Next Steps:{Colors.ENDC}")
    
    if all_passed:
        print("1. Deploy to Railway/Render using DEPLOYMENT.md guide")
        print("2. Update Postman collection with deployed URL")
        print("3. Test deployed API endpoints") 
        print("4. Create public GitHub Gist with Postman collection")
        print("5. Submit your project!")
    else:
        print("1. Fix the failing checks above")
        print("2. Re-run this script: python deployment_checklist.py")
        print("3. Continue with deployment once all checks pass")
    
    # Test deployed API if URL provided
    if len(sys.argv) > 1:
        deployed_url = sys.argv[1]
        print(f"\n{Colors.BLUE}Testing deployed API...{Colors.ENDC}")
        test_deployed_api(deployed_url)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Cancelled by user{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.RED}Error running checklist: {str(e)}{Colors.ENDC}")
        sys.exit(1)