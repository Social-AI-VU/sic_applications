"""
Helper script to verify Dialogflow CX agent configuration and find the correct agent ID and location.
"""

import json
from os.path import abspath, join
from google.cloud import dialogflowcx_v3
from google.oauth2.service_account import Credentials

def list_agents():
    """List all Dialogflow CX agents in the project to find the correct agent ID."""
    
    print("=" * 80)
    print("Dialogflow CX Agent Verification Tool")
    print("=" * 80)
    
    # Load credentials
    try:
        with open(abspath(join("..", "..", "conf", "google", "google-key.json"))) as f:
            keyfile_json = json.load(f)
        print(f"✓ Loaded credentials for project: {keyfile_json['project_id']}")
    except Exception as e:
        print(f"✗ Error loading credentials: {e}")
        return
    
    project_id = keyfile_json["project_id"]
    credentials = Credentials.from_service_account_info(keyfile_json)
    
    # Try different locations with their specific API endpoints
    locations = [
        ("global", "dialogflow.googleapis.com"),
        ("us-central1", "us-central1-dialogflow.googleapis.com"),
        ("us-east1", "us-east1-dialogflow.googleapis.com"),
        ("europe-west1", "europe-west1-dialogflow.googleapis.com"),
        ("europe-west2", "europe-west2-dialogflow.googleapis.com"),
        ("europe-west4", "europe-west4-dialogflow.googleapis.com"),
        ("asia-northeast1", "asia-northeast1-dialogflow.googleapis.com"),
    ]
    
    print(f"\nSearching for agents in project '{project_id}'...\n")
    
    found_agents = []
    
    for location, api_endpoint in locations:
        try:
            # For regional locations, use region-specific endpoints
            client_options = {"api_endpoint": api_endpoint}
            agents_client = dialogflowcx_v3.AgentsClient(
                credentials=credentials,
                client_options=client_options
            )
            
            parent = f"projects/{project_id}/locations/{location}"
            print(f"Checking location: {location:<20} (endpoint: {api_endpoint})...", end=" ")
            
            request = dialogflowcx_v3.ListAgentsRequest(parent=parent)
            response = agents_client.list_agents(request=request)
            
            agents_in_location = list(response)
            
            if agents_in_location:
                print(f"✓ Found {len(agents_in_location)} agent(s)")
                for agent in agents_in_location:
                    # Extract agent ID from name
                    # Format: projects/{project}/locations/{location}/agents/{agent_id}
                    parts = agent.name.split("/")
                    agent_id = parts[-1] if len(parts) > 0 else "unknown"
                    agent_location = parts[3] if len(parts) > 3 else "unknown"
                    
                    found_agents.append({
                        "name": agent.display_name,
                        "id": agent_id,
                        "location": agent_location,
                        "api_endpoint": api_endpoint,
                        "full_name": agent.name,
                        "default_language": agent.default_language_code,
                        "time_zone": agent.time_zone,
                    })
            else:
                print("No agents found")
                
        except Exception as e:
            print(f"✗ Error: {str(e)[:100]}")
    
    if found_agents:
        print("\n" + "=" * 80)
        print("FOUND AGENTS:")
        print("=" * 80)
        
        for i, agent in enumerate(found_agents, 1):
            print(f"\nAgent #{i}:")
            print(f"  Display Name:  {agent['name']}")
            print(f"  Agent ID:      {agent['id']}")
            print(f"  Location:      {agent['location']}")
            print(f"  API Endpoint:  {agent['api_endpoint']}")
            print(f"  Language:      {agent['default_language']}")
            print(f"  Time Zone:     {agent['time_zone']}")
            print(f"  Full Path:     {agent['full_name']}")
            
        print("\n" + "=" * 80)
        print("CONFIGURATION FOR YOUR DEMO:")
        print("=" * 80)
        
        # Use the first agent as example
        agent = found_agents[0]
        print(f"\nUpdate these values in your demo file:")
        print(f"  agent_id = \"{agent['id']}\"")
        print(f"  location = \"{agent['location']}\"")
        
        if agent['default_language']:
            lang_code = agent['default_language']
            print(f"  language = \"{lang_code}\"")
        
        print("\nSession path format:")
        print(f"  projects/{project_id}/locations/{agent['location']}/agents/{agent['id']}/sessions/{{session_id}}")
        
    else:
        print("\n" + "=" * 80)
        print("NO AGENTS FOUND")
        print("=" * 80)
        print("\nPossible reasons:")
        print("  1. No Dialogflow CX agents exist in this project")
        print("  2. The service account doesn't have permission to list agents")
        print("  3. You need to create an agent at: https://dialogflow.cloud.google.com/cx/")
        print("\nRequired permissions:")
        print("  - Dialogflow API Client")
        print("  - Or Dialogflow CX Agent Editor/Admin")


if __name__ == "__main__":
    list_agents()

