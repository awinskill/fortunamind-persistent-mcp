#!/usr/bin/env python3
"""
FortunaMind Persistent MCP Client Integration Examples

This module demonstrates how to integrate with the FortunaMind Persistent MCP Server
for applications requiring persistent trading journal and analytics capabilities.
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FortunaMindPersistentClient:
    """
    Client for interacting with FortunaMind Persistent MCP Server.
    
    Provides methods for journal management, user validation, and analytics
    with proper error handling and authentication.
    """
    
    def __init__(
        self,
        server_url: str = "https://fortunamind-persistent-mcp.onrender.com",
        user_email: str = None,
        subscription_key: str = None,
        timeout: int = 30
    ):
        """
        Initialize the persistent MCP client.
        
        Args:
            server_url: URL of the FortunaMind Persistent MCP Server
            user_email: User's email address for identity
            subscription_key: Valid subscription key (fm_sub_xxx format)
            timeout: Request timeout in seconds
        """
        self.server_url = server_url.rstrip('/')
        self.user_email = user_email or os.getenv('FORTUNAMIND_USER_EMAIL')
        self.subscription_key = subscription_key or os.getenv('FORTUNAMIND_SUBSCRIPTION_KEY')
        self.timeout = timeout
        
        # HTTP client with timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        
        # Validate required credentials
        if not self.user_email or not self.subscription_key:
            logger.warning("Missing credentials - set FORTUNAMIND_USER_EMAIL and FORTUNAMIND_SUBSCRIPTION_KEY")
    
    def _get_headers(self, **extra_headers) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {
            "Content-Type": "application/json",
            "X-User-Email": self.user_email,
            "X-Subscription-Key": self.subscription_key,
        }
        headers.update(extra_headers)
        return headers
    
    async def validate_subscription(self) -> Dict[str, Any]:
        """
        Validate user subscription and get user context.
        
        Returns:
            Dict with validation result and user context
        """
        try:
            response = await self.client.post(
                f"{self.server_url}/validate_subscription",
                headers=self._get_headers(),
                json={}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Subscription validation failed: {e}")
            return {"success": False, "valid": False, "error": str(e)}
    
    async def store_journal_entry(
        self,
        entry: str,
        entry_type: str = "general",
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Store a trading journal entry.
        
        Args:
            entry: Journal entry content
            entry_type: Type of entry (trade, analysis, reflection, etc.)
            tags: Optional tags for categorization
            metadata: Additional metadata (trade_id, symbol, etc.)
            
        Returns:
            Dict with storage result and entry ID
        """
        entry_data = {
            "entry": entry,
            "metadata": {
                "entry_type": entry_type,
                "tags": tags or [],
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
        }
        
        try:
            response = await self.client.post(
                f"{self.server_url}/store_journal_entry",
                headers=self._get_headers(),
                json=entry_data
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Journal entry stored with ID: {result.get('entry_id', 'unknown')}")
            return result
        except httpx.HTTPError as e:
            logger.error(f"Failed to store journal entry: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_journal_entries(
        self,
        limit: int = 20,
        offset: int = 0,
        entry_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve journal entries.
        
        Args:
            limit: Maximum number of entries to retrieve
            offset: Number of entries to skip
            entry_type: Filter by entry type
            
        Returns:
            Dict with entries list and count
        """
        params = {"limit": limit, "offset": offset}
        if entry_type:
            params["entry_type"] = entry_type
        
        try:
            response = await self.client.get(
                f"{self.server_url}/get_journal_entries",
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Retrieved {len(result.get('entries', []))} journal entries")
            return result
        except httpx.HTTPError as e:
            logger.error(f"Failed to retrieve journal entries: {e}")
            return {"success": False, "entries": [], "error": str(e)}
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """
        Get user statistics and usage information.
        
        Returns:
            Dict with user stats and usage metrics
        """
        try:
            response = await self.client.get(
                f"{self.server_url}/user_stats",
                headers=self._get_headers()
            )
            response.raise_for_status()
            result = response.json()
            logger.info("Retrieved user statistics")
            return result
        except httpx.HTTPError as e:
            logger.error(f"Failed to get user stats: {e}")
            return {"success": False, "error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check server health status.
        
        Returns:
            Dict with health status information
        """
        try:
            response = await self.client.get(f"{self.server_url}/status")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Health check failed: {e}")
            return {"overall": "unhealthy", "error": str(e)}
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


class TradingJournalManager:
    """
    High-level trading journal management using the persistent MCP client.
    
    Provides convenience methods for common trading journal operations.
    """
    
    def __init__(self, client: FortunaMindPersistentClient):
        self.client = client
    
    async def log_trade_entry(
        self,
        symbol: str,
        action: str,  # "buy" or "sell"
        quantity: float,
        price: float,
        reasoning: str,
        strategy: str = None
    ) -> Dict[str, Any]:
        """
        Log a trade entry with structured metadata.
        
        Args:
            symbol: Trading symbol (e.g., "BTC-USD")
            action: Trade action ("buy" or "sell")
            quantity: Quantity traded
            price: Trade price
            reasoning: Reasoning for the trade
            strategy: Trading strategy used
            
        Returns:
            Dict with storage result
        """
        entry = f"Trade: {action.upper()} {quantity} {symbol} @ ${price:.2f}\n\nReasoning: {reasoning}"
        
        metadata = {
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "price": price,
            "strategy": strategy,
            "trade_value": quantity * price
        }
        
        return await self.client.store_journal_entry(
            entry=entry,
            entry_type="trade",
            tags=[symbol, action, strategy] if strategy else [symbol, action],
            metadata=metadata
        )
    
    async def log_analysis_entry(
        self,
        symbol: str,
        analysis: str,
        outlook: str = None,
        confidence: int = None
    ) -> Dict[str, Any]:
        """
        Log a market analysis entry.
        
        Args:
            symbol: Symbol being analyzed
            analysis: Market analysis content
            outlook: Bullish/Bearish/Neutral outlook
            confidence: Confidence level (1-10)
            
        Returns:
            Dict with storage result
        """
        entry = f"Analysis: {symbol}\n\n{analysis}"
        if outlook:
            entry += f"\n\nOutlook: {outlook}"
        if confidence:
            entry += f"\nConfidence: {confidence}/10"
        
        metadata = {
            "symbol": symbol,
            "outlook": outlook,
            "confidence": confidence
        }
        
        return await self.client.store_journal_entry(
            entry=entry,
            entry_type="analysis",
            tags=[symbol, "analysis", outlook] if outlook else [symbol, "analysis"],
            metadata=metadata
        )
    
    async def log_reflection(self, content: str, tags: List[str] = None) -> Dict[str, Any]:
        """
        Log a trading reflection or learning entry.
        
        Args:
            content: Reflection content
            tags: Optional tags for categorization
            
        Returns:
            Dict with storage result
        """
        return await self.client.store_journal_entry(
            entry=content,
            entry_type="reflection",
            tags=tags or ["reflection"]
        )
    
    async def get_trades_for_symbol(self, symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all trade entries for a specific symbol.
        
        Args:
            symbol: Trading symbol to filter by
            limit: Maximum entries to return
            
        Returns:
            List of trade entries for the symbol
        """
        result = await self.client.get_journal_entries(
            limit=limit,
            entry_type="trade"
        )
        
        if not result.get("success", False):
            return []
        
        # Filter entries by symbol (client-side filtering)
        symbol_trades = []
        for entry in result.get("entries", []):
            metadata = entry.get("metadata", {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    continue
            
            if metadata.get("symbol") == symbol:
                symbol_trades.append(entry)
        
        return symbol_trades


# Example usage and integration patterns
async def example_basic_usage():
    """Example: Basic client usage"""
    print("=== Basic FortunaMind Persistent MCP Client Usage ===")
    
    # Initialize client (credentials from environment variables)
    async with FortunaMindPersistentClient() as client:
        # Check subscription status
        validation = await client.validate_subscription()
        print(f"Subscription valid: {validation.get('valid', False)}")
        
        # Store a journal entry
        result = await client.store_journal_entry(
            entry="Analyzed BTC market conditions. Seeing strong support at $42,000.",
            entry_type="analysis",
            tags=["BTC", "analysis", "support"],
            metadata={"symbol": "BTC-USD", "price_level": 42000}
        )
        print(f"Entry stored: {result.get('success', False)}")
        
        # Retrieve recent entries
        entries = await client.get_journal_entries(limit=5)
        print(f"Retrieved {len(entries.get('entries', []))} entries")


async def example_trading_journal():
    """Example: Using the trading journal manager"""
    print("=== Trading Journal Manager Example ===")
    
    async with FortunaMindPersistentClient() as client:
        journal = TradingJournalManager(client)
        
        # Log a trade
        trade_result = await journal.log_trade_entry(
            symbol="BTC-USD",
            action="buy",
            quantity=0.1,
            price=42500.00,
            reasoning="Strong support level, RSI oversold, bullish divergence on 4H chart",
            strategy="support_bounce"
        )
        print(f"Trade logged: {trade_result.get('success', False)}")
        
        # Log market analysis
        analysis_result = await journal.log_analysis_entry(
            symbol="ETH-USD",
            analysis="Ethereum showing strength against Bitcoin. Layer 2 adoption increasing.",
            outlook="bullish",
            confidence=7
        )
        print(f"Analysis logged: {analysis_result.get('success', False)}")
        
        # Log a reflection
        reflection_result = await journal.log_reflection(
            content="Need to improve risk management. Position sizes too large on recent trades.",
            tags=["risk_management", "lessons_learned"]
        )
        print(f"Reflection logged: {reflection_result.get('success', False)}")


async def example_portfolio_integration():
    """Example: Integration with portfolio tracking"""
    print("=== Portfolio Integration Example ===")
    
    async with FortunaMindPersistentClient() as client:
        journal = TradingJournalManager(client)
        
        # Simulate portfolio positions
        positions = [
            {"symbol": "BTC-USD", "quantity": 0.5, "avg_price": 41000},
            {"symbol": "ETH-USD", "quantity": 2.0, "avg_price": 2800}
        ]
        
        # Log portfolio snapshot
        portfolio_entry = f"Portfolio Update:\n"
        for pos in positions:
            current_value = pos["quantity"] * pos["avg_price"]
            portfolio_entry += f"- {pos['symbol']}: {pos['quantity']} @ ${pos['avg_price']:,} = ${current_value:,.2f}\n"
        
        await client.store_journal_entry(
            entry=portfolio_entry,
            entry_type="portfolio_snapshot",
            tags=["portfolio", "snapshot"],
            metadata={
                "positions": positions,
                "total_positions": len(positions),
                "snapshot_date": datetime.utcnow().isoformat()
            }
        )
        print("Portfolio snapshot logged")


async def example_batch_operations():
    """Example: Batch operations and error handling"""
    print("=== Batch Operations Example ===")
    
    async with FortunaMindPersistentClient() as client:
        # Batch store multiple entries
        entries = [
            ("Market looking volatile today", "market_observation"),
            ("Set stop losses on all positions", "risk_management"),
            ("Research DeFi protocols for next allocation", "research_task")
        ]
        
        results = []
        for entry_text, entry_type in entries:
            result = await client.store_journal_entry(
                entry=entry_text,
                entry_type=entry_type,
                tags=[entry_type]
            )
            results.append(result)
        
        successful = sum(1 for r in results if r.get("success", False))
        print(f"Batch operation: {successful}/{len(entries)} entries stored successfully")


async def main():
    """Run all examples"""
    print("FortunaMind Persistent MCP Client Examples")
    print("=" * 50)
    
    try:
        await example_basic_usage()
        print("\n")
        await example_trading_journal() 
        print("\n")
        await example_portfolio_integration()
        print("\n")
        await example_batch_operations()
        
    except Exception as e:
        print(f"Example failed: {e}")
        logger.error(f"Example execution error: {e}", exc_info=True)


if __name__ == "__main__":
    # Set up example credentials (replace with real values)
    os.environ.setdefault('FORTUNAMIND_USER_EMAIL', 'example@domain.com')
    os.environ.setdefault('FORTUNAMIND_SUBSCRIPTION_KEY', 'fm_sub_example_key_123')
    
    print("Note: Update environment variables with real credentials to run examples")
    print("FORTUNAMIND_USER_EMAIL and FORTUNAMIND_SUBSCRIPTION_KEY")
    print()
    
    asyncio.run(main())