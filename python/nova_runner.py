#!/usr/bin/env python3
"""
nova_runner.py
Paper-thin wrapper for Nova Act that receives JSON on stdin and prints result on stdout.
"""

import json
import os
import sys
import asyncio
from nova_act import NovaAct

def main():
    try:
        # Read JSON payload from stdin
        payload = json.loads(sys.stdin.read())
        prompt = payload["prompt"]
        url = payload.get("url", "about:blank")
        schema = payload.get("schema")  # optional
        headless = payload.get("headless", True)
        timeout = payload.get("timeout", 300)
        
        # Ensure API key is set
        if not os.getenv("NOVA_ACT_API_KEY"):
            raise Exception("NOVA_ACT_API_KEY environment variable is required")
        
        # Run Nova Act
        with NovaAct(starting_page=url, headless=headless) as nova:
            if schema:
                # If schema provided, use extract method
                result = nova.extract(schema)
            else:
                # Otherwise use act method
                result = nova.act(prompt)
            
            # Convert result to JSON-serializable format
            if hasattr(result, 'model_dump'):
                try:
                    output = result.model_dump(mode="json")
                except:
                    output = {"result": str(result)}
            elif hasattr(result, '__dict__'):
                try:
                    output = {k: str(v) for k, v in result.__dict__.items()}
                except:
                    output = {"result": str(result)}
            else:
                output = {"result": str(result)}
            
            # Add success flag
            output["success"] = True
            output["prompt"] = prompt
            output["url"] = url
            
            print(json.dumps(output))
            
    except Exception as e:
        # Return error in JSON format
        error_output = {
            "success": False,
            "error": str(e),
            "prompt": payload.get("prompt", "") if 'payload' in locals() else "",
            "url": payload.get("url", "") if 'payload' in locals() else ""
        }
        print(json.dumps(error_output))
        sys.exit(1)

if __name__ == "__main__":
    main()