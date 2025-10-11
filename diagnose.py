"""
Diagnostic script to test GCP Vertex AI configuration
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("GCP Vertex AI Configuration Diagnostics")
print("=" * 60)

# Check 1: Environment variables
print("\n1. Environment Variables:")
print("-" * 60)
gcp_project = os.getenv("GCP_PROJECT_ID")
gcp_location = os.getenv("GCP_LOCATION", "us-central1")

print(f"GCP_PROJECT_ID: {gcp_project if gcp_project else '❌ NOT SET'}")
print(f"GCP_LOCATION: {gcp_location}")

if not gcp_project:
    print("\n⚠️  ERROR: GCP_PROJECT_ID is not set in .env file")
    sys.exit(1)

# Check 2: Application Default Credentials
print("\n2. Application Default Credentials:")
print("-" * 60)
adc_path = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
if os.name == 'nt':  # Windows
    adc_path = os.path.expandvars("%APPDATA%\\gcloud\\application_default_credentials.json")

if os.path.exists(adc_path):
    print(f"✓ ADC file found at: {adc_path}")
else:
    print(f"❌ ADC file NOT found at: {adc_path}")
    print("\nPlease run: gcloud auth application-default login")
    sys.exit(1)

# Check 3: Test gcloud CLI
print("\n3. Testing gcloud CLI:")
print("-" * 60)
try:
    import subprocess
    
    # Check gcloud is installed
    result = subprocess.run(
        ["gcloud", "--version"],
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0:
        print("✓ gcloud CLI is installed")
        print(f"  Version: {result.stdout.split()[0]}")
    else:
        print("❌ gcloud CLI not found or not working")
except Exception as e:
    print(f"❌ Error checking gcloud: {e}")

# Check 4: Verify current project
print("\n4. Current gcloud project:")
print("-" * 60)
try:
    result = subprocess.run(
        ["gcloud", "config", "get-value", "project"],
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0:
        current_project = result.stdout.strip()
        print(f"Current project: {current_project}")
        if current_project != gcp_project:
            print(f"⚠️  WARNING: Current project ({current_project}) differs from .env ({gcp_project})")
    else:
        print("❌ Could not get current project")
except Exception as e:
    print(f"❌ Error: {e}")

# Check 5: Test Vertex AI API access
print("\n5. Testing Vertex AI API:")
print("-" * 60)
try:
    from google.cloud import aiplatform
    
    # Initialize with your project
    aiplatform.init(project=gcp_project, location=gcp_location)
    print(f"✓ Successfully initialized aiplatform client")
    print(f"  Project: {gcp_project}")
    print(f"  Location: {gcp_location}")
    
except ImportError:
    print("❌ google-cloud-aiplatform not installed")
    print("   Run: pip install -r requirements.txt")
except Exception as e:
    print(f"❌ Error initializing aiplatform: {e}")

# Check 6: Test VertexAI LLM initialization
print("\n6. Testing VertexAI LLM:")
print("-" * 60)
try:
    from langchain_google_vertexai import VertexAI
    
    # Try to initialize the LLM
    llm = VertexAI(
        model_name="text-bison@001",
        project=gcp_project,
        location=gcp_location,
        max_output_tokens=256,
        temperature=0.2,
    )
    print("✓ VertexAI LLM initialized successfully")
    
    # Try a simple test
    print("\n7. Testing LLM with a simple query:")
    print("-" * 60)
    try:
        response = llm.invoke("Say 'Hello, World!' in one sentence.")
        print(f"✓ LLM Response: {response}")
    except Exception as e:
        print(f"❌ Error invoking LLM: {e}")
        print(f"\nError type: {type(e).__name__}")
        print(f"Error details: {str(e)}")
        
        # Check if it's an API not enabled error
        if "403" in str(e):
            print("\n⚠️  This looks like a permissions or API enablement issue.")
            print("   Try running: gcloud services enable aiplatform.googleapis.com")
        elif "404" in str(e):
            print("\n⚠️  This is a 404 error - the endpoint was not found.")
            print("   Possible causes:")
            print("   1. The model name 'text-bison@001' might not be available in your region")
            print("   2. The Vertex AI API might not be enabled")
            print("   3. The project ID or location might be incorrect")
            print("\n   Try these commands:")
            print(f"   gcloud services enable aiplatform.googleapis.com --project={gcp_project}")
            print(f"   gcloud ai models list --region={gcp_location} --project={gcp_project}")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Run: pip install -r requirements.txt")
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"   Error type: {type(e).__name__}")

# Check 8: List available models
print("\n8. Checking available models:")
print("-" * 60)
try:
    result = subprocess.run(
        ["gcloud", "ai", "models", "list", 
         f"--region={gcp_location}", 
         f"--project={gcp_project}"],
        capture_output=True,
        text=True,
        timeout=30
    )
    if result.returncode == 0:
        print("✓ Available models:")
        print(result.stdout[:500])  # First 500 chars
    else:
        print(f"❌ Error listing models: {result.stderr}")
except Exception as e:
    print(f"⚠️  Could not list models: {e}")

print("\n" + "=" * 60)
print("Diagnostics complete!")
print("=" * 60)
