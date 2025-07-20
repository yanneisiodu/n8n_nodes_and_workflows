#!/usr/bin/env python3
"""
nova_runner.py
Enhanced Nova Act wrapper with structured data extraction, screenshots, and comprehensive logging.
"""

import json
import os
import sys
import base64
import datetime
import traceback
import tempfile
from typing import Dict, Any, List, Optional
from nova_act import NovaAct
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

def log_with_timestamp(message: str, execution_logs: List[str]) -> None:
    """Add timestamped log entry."""
    timestamp = datetime.datetime.now().isoformat()
    log_entry = f"[{timestamp}] {message}"
    execution_logs.append(log_entry)

def capture_screenshot_via_playwright(url: str, description: str, execution_logs: List[str]) -> Optional[Dict[str, Any]]:
    """Capture screenshot using Playwright and return as base64 string."""
    try:
        if not PLAYWRIGHT_AVAILABLE:
            log_with_timestamp("Playwright not available for screenshot capture", execution_logs)
            return None
            
        log_with_timestamp(f"Attempting screenshot capture: {description}", execution_logs)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            page.wait_for_load_state('networkidle')
            
            # Take screenshot
            screenshot_bytes = page.screenshot(full_page=True)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Get page info
            page_title = page.title()
            current_url = page.url
            
            browser.close()
            
            log_with_timestamp(f"Screenshot captured successfully: {len(screenshot_b64)} chars", execution_logs)
            
            return {
                "type": "full_page",
                "description": description,
                "timestamp": datetime.datetime.now().isoformat(),
                "data": f"data:image/png;base64,{screenshot_b64}",
                "page_title": page_title,
                "url": current_url
            }
            
    except Exception as e:
        log_with_timestamp(f"Screenshot capture failed: {str(e)}", execution_logs)
        return None

def parse_screenshot_commands(prompt: str) -> bool:
    """Check if prompt contains screenshot commands."""
    screenshot_keywords = [
        'screenshot', 'capture', 'take a picture', 'snap', 'image',
        'screenshot of', 'capture the', 'take image'
    ]
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in screenshot_keywords)

def auto_generate_schema(prompt: str, url: str) -> Optional[Dict[str, Any]]:
    """Auto-generate schema based on prompt content and URL patterns."""
    prompt_lower = prompt.lower()
    url_lower = url.lower()
    
    # E-commerce product patterns
    if any(keyword in prompt_lower for keyword in ['product', 'price', 'buy', 'shop', 'cart']):
        if 'amazon' in url_lower:
            return {
                "products": [
                    {
                        "title": "string",
                        "price": "string", 
                        "rating": "number",
                        "reviews_count": "string",
                        "availability": "string",
                        "image_url": "string"
                    }
                ]
            }
        else:
            return {
                "products": [
                    {
                        "name": "string",
                        "price": "string",
                        "description": "string"
                    }
                ]
            }
    
    # Search results patterns
    if any(keyword in prompt_lower for keyword in ['search', 'results', 'find', 'list']):
        return {
            "results": [
                {
                    "title": "string",
                    "url": "string",
                    "description": "string"
                }
            ]
        }
    
    # News/articles patterns
    if any(keyword in prompt_lower for keyword in ['news', 'article', 'headline', 'story']):
        return {
            "articles": [
                {
                    "headline": "string",
                    "summary": "string",
                    "author": "string",
                    "date": "string",
                    "url": "string"
                }
            ]
        }
    
    # Form data patterns
    if any(keyword in prompt_lower for keyword in ['form', 'input', 'field', 'submit']):
        return {
            "form_data": {
                "fields": [
                    {
                        "name": "string",
                        "type": "string",
                        "value": "string",
                        "required": "boolean"
                    }
                ]
            }
        }
    
    # Social media patterns
    if any(keyword in prompt_lower for keyword in ['post', 'tweet', 'comment', 'like', 'share']):
        return {
            "posts": [
                {
                    "content": "string",
                    "author": "string",
                    "timestamp": "string",
                    "likes": "number",
                    "comments": "number"
                }
            ]
        }
    
    # Generic data extraction
    return {
        "data": [
            {
                "text": "string",
                "value": "string"
            }
        ]
    }

def process_nova_result(result: Any) -> Dict[str, Any]:
    """Process Nova Act result and extract all available information."""
    output = {}
    
    # Debug: Log all available attributes
    result_attrs = [attr for attr in dir(result) if not attr.startswith('_')]
    
    # Handle different result types
    if hasattr(result, 'parsed_response'):
        output["parsed_response"] = result.parsed_response
        
    if hasattr(result, 'response'):
        output["response"] = result.response
        
    if hasattr(result, 'matches_schema'):
        output["matches_schema"] = result.matches_schema
        
    if hasattr(result, 'valid_json'):
        output["valid_json"] = result.valid_json
        
    if hasattr(result, 'metadata'):
        output["metadata"] = str(result.metadata)
        
    # Store all available attributes for debugging
    output["available_attributes"] = result_attrs
    
    # Store raw result as string fallback
    output["raw_result"] = str(result)
    
    return output

def extract_structured_data(result: Any) -> Dict[str, Any]:
    """Extract structured data from Nova Act result."""
    output = {}
    
    # Handle ActResult object with proper attribute extraction
    if hasattr(result, 'parsed_response') and result.parsed_response is not None:
        output["extracted_data"] = result.parsed_response
        output["data_type"] = "structured"
    elif hasattr(result, 'response') and result.response is not None:
        output["extracted_data"] = result.response
        output["data_type"] = "response"
    else:
        output["extracted_data"] = str(result)
        output["data_type"] = "raw"
    
    # Extract validation information
    if hasattr(result, 'matches_schema'):
        output["validation"] = {
            "matches_schema": result.matches_schema,
            "schema_valid": bool(result.matches_schema)
        }
    
    # Extract metadata if available
    if hasattr(result, 'metadata'):
        try:
            metadata_str = str(result.metadata)
            output["metadata"] = metadata_str
        except:
            output["metadata"] = "Metadata unavailable"
    
    return output

def main():
    execution_logs = []
    screenshots = []
    start_time = datetime.datetime.now()
    
    try:
        log_with_timestamp("Starting Nova Act execution", execution_logs)
        
        # Read JSON payload from stdin
        payload = json.loads(sys.stdin.read())
        operation = payload.get("operation", "action")
        prompt = payload["prompt"]
        url = payload.get("url", "about:blank")
        schema = payload.get("schema")  # optional for some operations
        headless = payload.get("headless", True)
        timeout = payload.get("timeout", 300)
        api_key = payload.get("api_key")
        
        # Options for enhanced outputs
        capture_screenshots = payload.get("capture_screenshots", True)
        detailed_logging = payload.get("detailed_logging", True)
        include_stack_trace = payload.get("include_stack_trace", False)
        
        log_with_timestamp(f"Configuration: operation={operation}, URL={url}, headless={headless}, schema_provided={bool(schema)}", execution_logs)
        
        # Parse screenshot requests from prompt
        screenshot_requested = parse_screenshot_commands(prompt)
        
        # Ensure API key is provided
        if not api_key:
            raise Exception("API key is required")
        
        # Set the API key in environment for Nova Act
        os.environ["NOVA_ACT_API_KEY"] = api_key
        log_with_timestamp("API key configured", execution_logs)
        
        # Take initial screenshot if requested
        if capture_screenshots and screenshot_requested:
            initial_screenshot = capture_screenshot_via_playwright(url, "Initial page load", execution_logs)
            if initial_screenshot:
                screenshots.append(initial_screenshot)
        
        # Run Nova Act
        log_with_timestamp("Initializing Nova Act browser session", execution_logs)
        result = None
        
        with NovaAct(starting_page=url, headless=headless) as nova:
            log_with_timestamp("Browser session started successfully", execution_logs)
            
            if operation == "action":
                # Pure action execution
                log_with_timestamp(f"Executing browser action: {prompt}", execution_logs)
                result = nova.act(prompt)
                log_with_timestamp("Browser action completed", execution_logs)
                
            elif operation == "extract":
                # Pure data extraction using act with schema
                extraction_schema = schema
                if not extraction_schema:
                    # Auto-generate schema if none provided
                    log_with_timestamp("No schema provided, auto-generating based on prompt and URL", execution_logs)
                    extraction_schema = auto_generate_schema(prompt, url)
                    log_with_timestamp(f"Auto-generated schema: {json.dumps(extraction_schema, indent=2)}", execution_logs)
                
                log_with_timestamp(f"Executing data extraction: {prompt}", execution_logs)
                result = nova.act(prompt, schema=extraction_schema)
                log_with_timestamp("Data extraction completed", execution_logs)
                
            elif operation == "action_extract":
                # Action followed by extraction
                extraction_schema = schema
                if not extraction_schema:
                    # Auto-generate schema if none provided
                    log_with_timestamp("No schema provided for extraction, auto-generating based on prompt and URL", execution_logs)
                    extraction_schema = auto_generate_schema(prompt, url)
                    log_with_timestamp(f"Auto-generated schema: {json.dumps(extraction_schema, indent=2)}", execution_logs)
                
                # First perform the action
                log_with_timestamp(f"Executing browser action: {prompt}", execution_logs)
                action_result = nova.act(prompt)
                log_with_timestamp("Browser action completed", execution_logs)
                
                # Then extract data using act with schema
                log_with_timestamp("Executing data extraction after action", execution_logs)
                result = nova.act("Extract data from this page", schema=extraction_schema)
                log_with_timestamp("Data extraction completed", execution_logs)
                
                # Store action result for reference (can't modify frozen result object)
                # result.action_result = action_result
            
            # Process Nova Act result comprehensively
            nova_output = process_nova_result(result)
            nova_output["operation_type"] = operation
            log_with_timestamp("Nova Act result processing completed", execution_logs)
        
        # Take final screenshot if requested
        if capture_screenshots and screenshot_requested:
            final_screenshot = capture_screenshot_via_playwright(url, "After execution", execution_logs)
            if final_screenshot:
                screenshots.append(final_screenshot)
            
        end_time = datetime.datetime.now()
        execution_duration = (end_time - start_time).total_seconds()
        
        # Build comprehensive output
        output = {
            "success": True,
            "prompt": prompt,
            "url": url,
            "execution_time_seconds": execution_duration,
            "timestamp": end_time.isoformat(),
            **nova_output
        }
        
        # Add optional outputs based on configuration
        if detailed_logging:
            output["execution_logs"] = execution_logs
            
        if capture_screenshots and screenshots:
            output["screenshots"] = screenshots
        elif capture_screenshots:
            output["screenshots"] = []  # Empty array to indicate feature was enabled but no screenshots captured
            
        log_with_timestamp(f"Execution completed successfully in {execution_duration:.2f} seconds", execution_logs)
        print(json.dumps(output, indent=2))
            
    except Exception as e:
        end_time = datetime.datetime.now()
        execution_duration = (end_time - start_time).total_seconds()
        
        log_with_timestamp(f"Error occurred: {str(e)}", execution_logs)
        
        # Return comprehensive error information
        error_output = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "execution_time_seconds": execution_duration,
            "timestamp": end_time.isoformat(),
            "prompt": payload.get("prompt", "") if 'payload' in locals() else "",
            "url": payload.get("url", "") if 'payload' in locals() else "",
            "execution_logs": execution_logs,
            "stack_trace": traceback.format_exc() if include_stack_trace else None
        }
        
        print(json.dumps(error_output, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()