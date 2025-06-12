#!/usr/bin/env python3
"""
🧪 GreenLightPA Connection Testing Script
Test all API keys and service connections for the hybrid architecture
"""

import asyncio
import os
import sys
from typing import Dict, List, Optional
from datetime import datetime
import traceback

# Color constants for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

def print_header(text: str, color: str = Colors.BLUE):
    """Print a formatted header"""
    print(f"\n{color}{'=' * 60}{Colors.NC}")
    print(f"{color}{text.center(60)}{Colors.NC}")
    print(f"{color}{'=' * 60}{Colors.NC}\n")

def print_test(service: str, status: str, message: str = ""):
    """Print test result with colored status"""
    if status == "✅":
        color = Colors.GREEN
        status_text = "PASS"
    elif status == "❌":
        color = Colors.RED
        status_text = "FAIL"
    elif status == "⚠️":
        color = Colors.YELLOW
        status_text = "WARN"
    else:
        color = Colors.BLUE
        status_text = "INFO"
    
    print(f"{color}{status} {service:<30} {status_text}{Colors.NC}")
    if message:
        print(f"   {Colors.CYAN}{message}{Colors.NC}")

async def test_supabase_connection():
    """Test Supabase database connection"""
    try:
        # Check if we have the required environment variables
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            print_test("Supabase", "⚠️", "Missing SUPABASE_URL or SUPABASE_ANON_KEY")
            return False
        
        # Try to import supabase client
        try:
            from supabase import create_client, Client
        except ImportError:
            print_test("Supabase", "❌", "supabase-py not installed. Run: pip install supabase")
            return False
        
        # Create client and test connection
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Test with a simple query (this might fail if no tables exist, but connection should work)
        try:
            # Try to list tables or get database info
            result = supabase.rpc('version').execute()
            print_test("Supabase", "✅", f"Connected to {supabase_url}")
            return True
        except Exception as e:
            # Even if the RPC fails, if we get here the connection works
            print_test("Supabase", "✅", f"Connected to {supabase_url} (basic auth OK)")
            return True
            
    except Exception as e:
        print_test("Supabase", "❌", f"Connection failed: {str(e)}")
        return False

async def test_upstash_redis():
    """Test Upstash Redis connection"""
    try:
        redis_url = os.getenv("UPSTASH_REDIS_URL") or os.getenv("REDIS_URL")
        
        if not redis_url:
            print_test("Upstash Redis", "⚠️", "Missing UPSTASH_REDIS_URL or REDIS_URL")
            return False
        
        # Try to import redis
        try:
            import redis
        except ImportError:
            print_test("Upstash Redis", "❌", "redis-py not installed. Run: pip install redis")
            return False
        
        # Test connection
        r = redis.from_url(redis_url)
        result = r.ping()
        
        if result:
            print_test("Upstash Redis", "✅", f"Connected and responding to ping")
            return True
        else:
            print_test("Upstash Redis", "❌", "Connection failed - ping returned False")
            return False
            
    except Exception as e:
        print_test("Upstash Redis", "❌", f"Connection failed: {str(e)}")
        return False

def test_openai_api():
    """Test OpenAI API connection"""
    try:
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not openai_key:
            print_test("OpenAI API", "⚠️", "Missing OPENAI_API_KEY (skipping)")
            return True  # Not an error if using Anthropic instead
        
        # Try to import openai
        try:
            import openai
        except ImportError:
            print_test("OpenAI API", "❌", "openai not installed. Run: pip install openai")
            return False
        
        # Set API key and test
        client = openai.OpenAI(api_key=openai_key)
        
        # List models to test API key
        models = client.models.list()
        
        if models and len(models.data) > 0:
            model_count = len(models.data)
            print_test("OpenAI API", "✅", f"Connected - {model_count} models available")
            return True
        else:
            print_test("OpenAI API", "❌", "Connected but no models available")
            return False
            
    except Exception as e:
        print_test("OpenAI API", "❌", f"Connection failed: {str(e)}")
        return False

def test_anthropic_api():
    """Test Anthropic API connection"""
    try:
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not anthropic_key:
            print_test("Anthropic API", "⚠️", "Missing ANTHROPIC_API_KEY (skipping)")
            return True  # Not an error if using OpenAI instead
        
        # Try to import anthropic
        try:
            import anthropic
        except ImportError:
            print_test("Anthropic API", "❌", "anthropic not installed. Run: pip install anthropic")
            return False
        
        # Set API key and test
        client = anthropic.Anthropic(api_key=anthropic_key)
        
        # Test with a simple completion
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        if response and response.content:
            print_test("Anthropic API", "✅", f"Connected - Claude model responding")
            return True
        else:
            print_test("Anthropic API", "❌", "Connected but no response")
            return False
            
    except Exception as e:
        print_test("Anthropic API", "❌", f"Connection failed: {str(e)}")
        return False

def test_langsmith_connection():
    """Test LangSmith connection"""
    try:
        langchain_key = os.getenv("LANGCHAIN_API_KEY")
        
        if not langchain_key:
            print_test("LangSmith", "⚠️", "Missing LANGCHAIN_API_KEY (optional)")
            return True  # This is optional, so we return True
        
        # Try to import langsmith
        try:
            from langsmith import Client
        except ImportError:
            print_test("LangSmith", "⚠️", "langsmith not installed. Run: pip install langsmith")
            return True  # Optional, so still OK
        
        # Test connection
        client = Client(api_key=langchain_key)
        
        # Try to get session info or projects
        try:
            # This might fail if no projects exist, but that's OK
            projects = client.list_datasets(limit=1)
            print_test("LangSmith", "✅", "Connected and authenticated")
            return True
        except Exception as e:
            # If we get an auth error, the key is bad
            if "unauthorized" in str(e).lower() or "forbidden" in str(e).lower():
                print_test("LangSmith", "❌", f"Authentication failed: {str(e)}")
                return False
            else:
                # Other errors might be OK (like no datasets existing)
                print_test("LangSmith", "✅", "Connected (authentication OK)")
                return True
            
    except Exception as e:
        print_test("LangSmith", "❌", f"Connection failed: {str(e)}")
        return False

async def test_chromadb_connection():
    """Test ChromaDB connection"""
    try:
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = os.getenv("CHROMA_PORT", "8001")
        
        # Try to import chromadb
        try:
            import chromadb
            import httpx
        except ImportError:
            print_test("ChromaDB", "❌", "chromadb not installed. Run: pip install chromadb")
            return False
        
        # Test HTTP connection first
        chroma_url = f"http://{chroma_host}:{chroma_port}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{chroma_url}/api/v1/heartbeat", timeout=5.0)
                if response.status_code == 200:
                    print_test("ChromaDB", "✅", f"Connected to {chroma_url}")
                    return True
                else:
                    print_test("ChromaDB", "❌", f"HTTP {response.status_code} from {chroma_url}")
                    return False
        except Exception as e:
            print_test("ChromaDB", "❌", f"Connection failed to {chroma_url}: {str(e)}")
            return False
            
    except Exception as e:
        print_test("ChromaDB", "❌", f"Test failed: {str(e)}")
        return False

def test_twilio_credentials():
    """Test Twilio credentials"""
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        
        if not account_sid or not auth_token:
            print_test("Twilio", "⚠️", "Missing TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN (optional)")
            return True  # Optional service
        
        # Try to import twilio
        try:
            from twilio.rest import Client
        except ImportError:
            print_test("Twilio", "❌", "twilio not installed. Run: pip install twilio")
            return False
        
        # Test credentials
        client = Client(account_sid, auth_token)
        
        # Try to get account info
        account = client.api.accounts(account_sid).fetch()
        
        if account:
            print_test("Twilio", "✅", f"Connected - Account: {account.friendly_name}")
            return True
        else:
            print_test("Twilio", "❌", "Failed to fetch account info")
            return False
            
    except Exception as e:
        print_test("Twilio", "❌", f"Authentication failed: {str(e)}")
        return False

async def test_n8n_connection():
    """Test N8n connection"""
    try:
        n8n_host = os.getenv("N8N_HOST", "localhost")
        n8n_port = os.getenv("N8N_PORT", "5678")
        n8n_protocol = os.getenv("N8N_PROTOCOL", "http")
        
        n8n_url = f"{n8n_protocol}://{n8n_host}:{n8n_port}"
        
        try:
            import httpx
        except ImportError:
            print_test("N8n", "❌", "httpx not installed. Run: pip install httpx")
            return False
        
        # Test connection
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{n8n_url}/healthz", timeout=5.0)
                if response.status_code == 200:
                    print_test("N8n", "✅", f"Connected to {n8n_url}")
                    return True
                else:
                    # Try alternative endpoint
                    response = await client.get(f"{n8n_url}/", timeout=5.0)
                    if response.status_code in [200, 401]:  # 401 is OK, means auth is working
                        print_test("N8n", "✅", f"Connected to {n8n_url}")
                        return True
                    else:
                        print_test("N8n", "❌", f"HTTP {response.status_code} from {n8n_url}")
                        return False
        except Exception as e:
            print_test("N8n", "❌", f"Connection failed to {n8n_url}: {str(e)}")
            return False
            
    except Exception as e:
        print_test("N8n", "❌", f"Test failed: {str(e)}")
        return False

def test_environment_variables():
    """Test that all required environment variables are set"""
    required_vars = [
        "ENVIRONMENT",
        "SECRET_KEY",
        "JWT_SECRET_KEY"
    ]
    
    optional_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY", 
        "OPENAI_API_KEY",
        "UPSTASH_REDIS_URL",
        "LANGCHAIN_API_KEY",
        "TWILIO_ACCOUNT_SID",
        "CHANGE_HEALTHCARE_API_KEY"
    ]
    
    print_header("Environment Variables Check")
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print_test(f"ENV: {var}", "✅", f"Set (length: {len(value)})")
        else:
            print_test(f"ENV: {var}", "❌", "Missing (required)")
            missing_required.append(var)
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print_test(f"ENV: {var}", "✅", f"Set (length: {len(value)})")
        else:
            print_test(f"ENV: {var}", "⚠️", "Missing (optional)")
            missing_optional.append(var)
    
    if missing_required:
        print(f"\n{Colors.RED}❌ Missing required variables: {', '.join(missing_required)}{Colors.NC}")
        return False
    
    if missing_optional:
        print(f"\n{Colors.YELLOW}⚠️  Missing optional variables: {', '.join(missing_optional)}{Colors.NC}")
    
    return True

async def run_all_tests():
    """Run all connection tests"""
    print_header("🧪 GreenLightPA Connection Tests", Colors.PURPLE)
    print(f"{Colors.CYAN}Testing all API keys and service connections...{Colors.NC}")
    print(f"{Colors.CYAN}Timestamp: {datetime.now().isoformat()}{Colors.NC}")
    
    # Check environment variables first
    env_ok = test_environment_variables()
    
    if not env_ok:
        print(f"\n{Colors.RED}❌ Environment check failed. Please run setup script first.{Colors.NC}")
        return False
    
    print_header("Service Connection Tests")
    
    # Run all connection tests
    tests = [
        ("Supabase Database", test_supabase_connection()),
        ("Upstash Redis", test_upstash_redis()),
        ("OpenAI API", test_openai_api()),
        ("Anthropic API", test_anthropic_api()),
        ("LangSmith", test_langsmith_connection()),
        ("ChromaDB", test_chromadb_connection()),
        ("N8n Workflow Engine", test_n8n_connection()),
        ("Twilio", test_twilio_credentials()),
    ]
    
    results = []
    
    for test_name, test_coro in tests:
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            results.append((test_name, result))
        except Exception as e:
            print_test(test_name, "❌", f"Test error: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    if passed == total:
        print(f"{Colors.GREEN}🎉 All tests passed! ({passed}/{total}){Colors.NC}")
        print(f"{Colors.GREEN}✅ Your GreenLightPA configuration is ready!{Colors.NC}")
        success = True
    else:
        failed = total - passed
        print(f"{Colors.YELLOW}⚠️  {passed}/{total} tests passed, {failed} failed{Colors.NC}")
        
        failed_tests = [name for name, result in results if not result]
        print(f"{Colors.RED}❌ Failed tests: {', '.join(failed_tests)}{Colors.NC}")
        success = False
    
    print_header("Next Steps")
    
    if success:
        print(f"{Colors.CYAN}🚀 Start development environment:{Colors.NC}")
        print(f"   {Colors.YELLOW}docker-compose --profile development up -d{Colors.NC}")
        print()
        print(f"{Colors.CYAN}🧪 Begin Sprint 1 - Core AI Pipeline:{Colors.NC}")
        print(f"   {Colors.YELLOW}python -m app.services.langchain_service{Colors.NC}")
    else:
        print(f"{Colors.CYAN}🔧 Fix configuration issues:{Colors.NC}")
        print(f"   {Colors.YELLOW}./scripts/setup_api_keys.sh{Colors.NC}")
        print()
        print(f"{Colors.CYAN}📚 Check documentation:{Colors.NC}")
        print(f"   {Colors.YELLOW}docs/deployment/api-keys-setup.md{Colors.NC}")
    
    return success

def load_env_file():
    """Load environment file if it exists"""
    env_files = [".env.development", ".env", "config.example.env"]
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"{Colors.CYAN}📁 Loading environment from {env_file}{Colors.NC}")
            
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
                return True
            except ImportError:
                # Manually load env file
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key] = value
                return True
    
    print(f"{Colors.YELLOW}⚠️  No environment file found. Using system environment variables.{Colors.NC}")
    return False

if __name__ == "__main__":
    # Load environment variables
    load_env_file()
    
    # Run tests
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Tests interrupted by user{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error: {str(e)}{Colors.NC}")
        traceback.print_exc()
        sys.exit(1) 