#!/usr/bin/env python3
"""
Amazon Nova Act Runner for n8n
This script bridges the n8n node with the Nova Act SDK
"""

import os
import sys
import json
import logging
import argparse
import traceback
from typing import Dict, List, Any, Optional
import tempfile
import datetime

try:
    from nova_act import NovaAct
except ImportError:
    print(json.dumps({
        "error": "nova-act package not installed. Run: pip install nova-act",
        "success": False
    }))
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('n8n_nova_act')

class NovaActRunner:
    def __init__(self, api_key: str):
        self.api_key = api_key
        os.environ['NOVA_ACT_API_KEY'] = api_key
        self.screenshots: List[str] = []
        
    def perform_actions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a series of browser actions using natural language commands"""
        commands = params.get('commands', '')
        starting_url = params.get('starting_url', '')
        headless = params.get('headless', True)
        timeout = params.get('timeout', 300)
        
        commands_list = [cmd.strip() for cmd in commands.split('\n') if cmd.strip()]
        
        if not commands_list:
            return {
                "success": False,
                "error": "No commands provided"
            }
        
        try:
            logger.info(f"🚀 Initializing NovaAct (Headless: {headless})")
            
            nova_kwargs = {'headless': headless}
            if starting_url:
                nova_kwargs['starting_page'] = starting_url
                
            with NovaAct(**nova_kwargs) as nova:
                logger.info("✅ NovaAct initialized successfully")
                executed_commands = []
                
                for i, command in enumerate(commands_list, 1):
                    logger.info(f"[{i}/{len(commands_list)}] Executing: '{command}'")
                    try:
                        result = nova.act(command)
                        executed_commands.append({
                            "command": command,
                            "success": True,
                            "result": str(result) if result else "Command executed successfully"
                        })
                    except Exception as cmd_error:
                        logger.error(f"Command failed: {command} - {str(cmd_error)}")
                        executed_commands.append({
                            "command": command,
                            "success": False,
                            "error": str(cmd_error)
                        })
                        # Continue with other commands instead of failing completely
                        
                # Always try to take a final screenshot for verification
                try:
                    screenshot_path = self._take_screenshot(nova)
                    if screenshot_path:
                        self.screenshots.append(screenshot_path)
                except Exception as screenshot_error:
                    logger.warning(f"Failed to take final screenshot: {screenshot_error}")
                
                return {
                    "success": True,
                    "executed_commands": executed_commands,
                    "screenshots": self.screenshots,
                    "message": f"Successfully executed {len([cmd for cmd in executed_commands if cmd['success']])} out of {len(commands_list)} commands"
                }
                
        except Exception as e:
            logger.error(f"❌ Nova Act execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc() if logger.level <= logging.DEBUG else None
            }
    
    def extract_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data from a webpage"""
        starting_url = params.get('starting_url', '')
        navigation_commands = params.get('navigation_commands', '')
        data_schema = params.get('data_schema', {})
        headless = params.get('headless', True)
        timeout = params.get('timeout', 300)
        
        if not starting_url:
            return {
                "success": False,
                "error": "starting_url is required for data extraction"
            }
        
        try:
            logger.info(f"🚀 Starting data extraction from {starting_url}")
            
            with NovaAct(starting_page=starting_url, headless=headless) as nova:
                logger.info("✅ NovaAct initialized for data extraction")
                
                # Execute navigation commands if provided
                if navigation_commands:
                    nav_commands = [cmd.strip() for cmd in navigation_commands.split('\n') if cmd.strip()]
                    for command in nav_commands:
                        logger.info(f"Navigation: {command}")
                        nova.act(command)
                
                # Extract data using the provided schema
                logger.info("🔍 Extracting data...")
                extracted_data = nova.extract(data_schema)
                
                # Take a screenshot for verification
                screenshot_path = self._take_screenshot(nova)
                if screenshot_path:
                    self.screenshots.append(screenshot_path)
                
                return {
                    "success": True,
                    "extracted_data": extracted_data,
                    "screenshots": self.screenshots,
                    "url": starting_url,
                    "schema_used": data_schema
                }
                
        except Exception as e:
            logger.error(f"❌ Data extraction failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "url": starting_url,
                "traceback": traceback.format_exc() if logger.level <= logging.DEBUG else None
            }
    
    def _take_screenshot(self, nova: NovaAct) -> Optional[str]:
        """Take a screenshot and return the file path"""
        try:
            # Create a timestamped filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_dir = os.path.join(tempfile.gettempdir(), 'nova_act_screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)
            
            screenshot_path = os.path.join(screenshot_dir, f"screenshot_{timestamp}.png")
            
            # Use Nova Act to take screenshot
            nova.act(f"take a screenshot and save it as {screenshot_path}")
            
            if os.path.exists(screenshot_path):
                logger.info(f"📸 Screenshot saved: {screenshot_path}")
                return screenshot_path
            else:
                logger.warning("Screenshot command executed but file not found")
                return None
                
        except Exception as e:
            logger.error(f"Failed to take screenshot: {str(e)}")
            return None

def main():
    parser = argparse.ArgumentParser(description="Nova Act Runner for n8n")
    parser.add_argument('--api_key', required=True, help='Amazon Nova Act API Key')
    parser.add_argument('--operation', required=True, 
                       choices=['perform_actions', 'extract_data'],
                       help='Operation to perform')
    parser.add_argument('--params', required=True, help='JSON parameters for the operation')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Parse parameters
        params = json.loads(args.params)
        
        # Initialize runner
        runner = NovaActRunner(args.api_key)
        
        # Execute operation
        if args.operation == 'perform_actions':
            result = runner.perform_actions(params)
        elif args.operation == 'extract_data':
            result = runner.extract_data(params)
        else:
            result = {
                "success": False,
                "error": f"Unknown operation: {args.operation}"
            }
        
        # Output result as JSON
        print(json.dumps(result, indent=2))
        
        # Exit with appropriate code
        sys.exit(0 if result.get('success', False) else 1)
        
    except json.JSONDecodeError as e:
        error_result = {
            "success": False,
            "error": f"Invalid JSON parameters: {str(e)}"
        }
        print(json.dumps(error_result))
        sys.exit(1)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc() if args.debug else None
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    main()