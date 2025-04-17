import requests
import json
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

def test_text_endpoint():
    """Test the text endpoint."""
    print("\n=== Testing Text Endpoint ===")
    
    # Prepare the request data
    data = {
        "user_id": "test-user-123",
        "message": "How do I create a business plan for my startup?",
        "context": []
    }
    
    # Make the request
    try:
        response = requests.post(f"{BASE_URL}/text", json=data)
        response.raise_for_status()
        
        # Print the response
        result = response.json()
        print(f"Response: {result['response']}")
        print("\nSuggestions:")
        for suggestion in result["suggestions"]:
            print(f"- {suggestion}")
        
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"Error: {str(e)}")
        return False

def test_suggestions_endpoint():
    """Test the suggestions endpoint."""
    print("\n=== Testing Suggestions Endpoint ===")
    
    # Prepare the request data
    data = {
        "user_id": "test-user-123",
        "message": "I'm interested in learning about startup funding options."
    }
    
    # Make the request
    try:
        response = requests.post(f"{BASE_URL}/suggestions", json=data)
        response.raise_for_status()
        
        # Print the response
        result = response.json()
        print("\nSuggestions:")
        for suggestion in result["suggestions"]:
            print(f"- {suggestion}")
        
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"Error: {str(e)}")
        return False

def main():
    """Run the tests."""
    print("Starting API tests...")
    
    # Test the text endpoint
    text_success = test_text_endpoint()
    
    # Test the suggestions endpoint
    suggestions_success = test_suggestions_endpoint()
    
    # Print the summary
    print("\n=== Test Summary ===")
    print(f"Text Endpoint: {'Success' if text_success else 'Failed'}")
    print(f"Suggestions Endpoint: {'Success' if suggestions_success else 'Failed'}")

if __name__ == "__main__":
    main()
