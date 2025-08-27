#!/usr/bin/env python3
"""
FortunaMind Persistent MCP HTTP Bridge (Static Version)

One-command installer bridge that proxies stdio MCP protocol to HTTP MCP server 
with both subscription and Coinbase API credential injection.

This bridge allows Claude Desktop to connect to the persistent MCP server
while automatically injecting both types of required credentials:
- Subscription credentials (email + subscription key)  
- Coinbase API credentials (api key + api secret)
"""

import asyncio
import json
import logging
import os
import ssl
import sys
import time
from typing import Any, Dict, Optional

import aiohttp

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s", 
    stream=sys.stderr
)

logger = logging.getLogger(__name__)


class PersistentMCPHTTPBridge:
    def __init__(
        self, 
        server_url: str,
        user_email: str,
        subscription_key: str,
        coinbase_api_key: str,
        coinbase_api_secret: str
    ):
        self.server_url = server_url
        self.user_email = user_email
        self.subscription_key = subscription_key
        self.coinbase_api_key = coinbase_api_key
        self.coinbase_api_secret = coinbase_api_secret
        self.session = None

    async def __aenter__(self):
        # Create SSL context that handles certificate verification properly
        ssl_context = ssl.create_default_context()
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _inject_credentials_into_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Inject credentials into MCP request based on method type"""
        
        # For tools/call requests, inject Coinbase credentials into tool arguments
        if request.get("method") == "tools/call" and "params" in request:
            params = request["params"]
            if "arguments" in params:
                args = params["arguments"]
                
                # Inject Coinbase API credentials if not already present
                if "api_key" not in args or not args["api_key"]:
                    args["api_key"] = self.coinbase_api_key
                if "api_secret" not in args or not args["api_secret"]:
                    args["api_secret"] = self.coinbase_api_secret
                
                # Also inject any other credentials that tools might need
                if "coinbase_api_key" not in args or not args["coinbase_api_key"]:
                    args["coinbase_api_key"] = self.coinbase_api_key
                if "coinbase_api_secret" not in args or not args["coinbase_api_secret"]:
                    args["coinbase_api_secret"] = self.coinbase_api_secret
        
        return request

    def _get_request_headers(self) -> Dict[str, str]:
        """Get HTTP headers with both subscription and Coinbase credentials"""
        return {
            "Content-Type": "application/json",
            # Subscription credentials
            "X-User-Email": self.user_email,
            "X-Subscription-Key": self.subscription_key,
            # Coinbase credentials  
            "X-Coinbase-Api-Key": self.coinbase_api_key,
            "X-Coinbase-Api-Secret": self.coinbase_api_secret,
            # Bridge identification
            "X-MCP-Bridge": "persistent-http-bridge/1.0",
            "User-Agent": "FortunaMind-Persistent-MCP-Bridge/1.0"
        }

    async def forward_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Forward MCP request to HTTP server with credential injection"""
        try:
            # Inject credentials into the request payload
            request_with_credentials = self._inject_credentials_into_request(request.copy())
            
            # Get headers with all credentials
            headers = self._get_request_headers()
            
            method = request.get("method", "unknown")
            logger.info(f"Forwarding {method} to {self.server_url}")
            
            # Log credential status (without exposing actual values)
            logger.debug(f"Credentials status:")
            logger.debug(f"  Email: {'✓' if self.user_email else '✗'}")
            logger.debug(f"  Subscription: {'✓' if self.subscription_key else '✗'}")  
            logger.debug(f"  Coinbase API Key: {'✓' if self.coinbase_api_key else '✗'}")
            logger.debug(f"  Coinbase API Secret: {'✓' if self.coinbase_api_secret else '✗'}")

            async with self.session.post(
                self.server_url,
                json=request_with_credentials,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Success: {method}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"HTTP {response.status}: {error_text}")
                    
                    # Try to parse error details for better debugging
                    error_detail = error_text
                    try:
                        error_json = json.loads(error_text)
                        if isinstance(error_json, dict) and 'detail' in error_json:
                            error_detail = error_json['detail']
                    except:
                        pass
                    
                    return {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32603,
                            "message": f"HTTP error {response.status}: {error_detail}",
                        },
                    }

        except asyncio.TimeoutError:
            logger.error(f"Timeout forwarding request: {request.get('method', 'unknown')}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32603, "message": "Request timeout"},
            }
        except Exception as e:
            logger.error(f"Error forwarding request: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32603, "message": f"Bridge error: {str(e)}"},
            }

    async def run(self):
        """Run the MCP bridge"""
        logger.info("🌉 Starting FortunaMind Persistent MCP HTTP Bridge")
        logger.info(f"🔗 Target server: {self.server_url}")
        logger.info(f"📧 User email: {self.user_email}")
        logger.info(f"🎫 Subscription key: {self.subscription_key[:20]}...{self.subscription_key[-4:]}" if self.subscription_key and len(self.subscription_key) > 24 else "🎫 Subscription key: None")
        logger.info(f"🔑 Coinbase API key: {self.coinbase_api_key[:30]}..." if self.coinbase_api_key else "🔑 Coinbase API key: None")
        logger.info(f"🔐 Coinbase API secret: {'*' * min(len(self.coinbase_api_secret) if self.coinbase_api_secret else 0, 50)}")

        while True:
            try:
                # Read JSON-RPC request from stdin
                line = sys.stdin.readline()
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                # Parse request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "Parse error"},
                    }
                    print(json.dumps(error_response), flush=True)
                    continue

                # Forward to HTTP server
                response = await self.forward_request(request)

                # Send response (skip notifications that don't need responses)
                if response is not None:
                    print(json.dumps(response), flush=True)

            except EOFError:
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Bridge error: {e}", exc_info=True)
                break

        logger.info("🌉 Persistent MCP HTTP Bridge shutting down")


async def main():
    """Main entry point"""
    # Get configuration from environment
    server_url = os.getenv("MCP_SERVER_URL", "https://fortunamind-persistent-mcp.onrender.com")
    
    # Subscription credentials
    user_email = os.getenv("FORTUNAMIND_USER_EMAIL")
    subscription_key = os.getenv("FORTUNAMIND_SUBSCRIPTION_KEY")
    
    # Coinbase credentials
    coinbase_api_key = os.getenv("COINBASE_API_KEY")
    coinbase_api_secret = os.getenv("COINBASE_API_SECRET")
    
    # Validate required credentials
    missing_credentials = []
    
    if not user_email:
        missing_credentials.append("FORTUNAMIND_USER_EMAIL")
    if not subscription_key:
        missing_credentials.append("FORTUNAMIND_SUBSCRIPTION_KEY")  
    if not coinbase_api_key:
        missing_credentials.append("COINBASE_API_KEY")
    if not coinbase_api_secret:
        missing_credentials.append("COINBASE_API_SECRET")
    
    if missing_credentials:
        logger.error("❌ Missing required environment variables:")
        for var in missing_credentials:
            logger.error(f"  - {var}")
        logger.error("")
        logger.error("💡 Set these in your Claude Desktop MCP configuration:")
        logger.error('  "env": {')
        logger.error('    "FORTUNAMIND_USER_EMAIL": "your-email@domain.com",')
        logger.error('    "FORTUNAMIND_SUBSCRIPTION_KEY": "fm_sub_your_key_here",')
        logger.error('    "COINBASE_API_KEY": "organizations/xxx/apiKeys/xxx",')
        logger.error('    "COINBASE_API_SECRET": "-----BEGIN EC PRIVATE KEY-----\\\\n..."')
        logger.error('  }')
        sys.exit(1)
    
    # Validate server URL format
    if not server_url.startswith(('http://', 'https://')):
        logger.error(f"❌ Invalid server URL: {server_url}")
        logger.error("💡 Server URL must start with http:// or https://")
        sys.exit(1)
    
    # Ensure server URL ends with /mcp for the MCP endpoint
    if not server_url.endswith('/mcp'):
        server_url = server_url + '/mcp'
    
    # Validate subscription key format
    if not subscription_key.startswith('fm_sub_'):
        logger.warning(f"⚠️  Subscription key doesn't match expected format (fm_sub_*)")
    
    # Validate Coinbase API key format
    if not coinbase_api_key.startswith('organizations/'):
        logger.warning(f"⚠️  Coinbase API key doesn't match expected format (organizations/*)")
    
    # Create and run bridge
    async with PersistentMCPHTTPBridge(
        server_url=server_url,
        user_email=user_email,
        subscription_key=subscription_key,
        coinbase_api_key=coinbase_api_key,
        coinbase_api_secret=coinbase_api_secret
    ) as bridge:
        await bridge.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bridge stopped by user")
    except Exception as e:
        logger.error(f"💥 Bridge failed: {e}", exc_info=True)
        sys.exit(1)