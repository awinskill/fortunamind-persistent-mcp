#!/usr/bin/env python3
"""
Claude Desktop MCP Integration Example

This example demonstrates how to create an MCP server that integrates
with FortunaMind Persistent MCP Server for Claude Desktop.
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional, Sequence
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Resource,
    Tool,
    TextContent,
    ListResourcesResult,
    ListResourcesRequest,
    ReadResourceRequest,
    ReadResourceResult,
)
import logging

# Import our persistent client
from client_integration import FortunaMindPersistentClient, TradingJournalManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MCP Server instance
server = Server("fortunamind-persistent")


class FortunaMindMCPWrapper:
    """
    Wrapper to integrate FortunaMind Persistent MCP with standard MCP protocol.
    
    This allows Claude Desktop to use persistent trading journal capabilities
    through the standard MCP interface.
    """
    
    def __init__(self):
        self.client: Optional[FortunaMindPersistentClient] = None
        self.journal: Optional[TradingJournalManager] = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize the persistent client"""
        try:
            self.client = FortunaMindPersistentClient(
                user_email=os.getenv('FORTUNAMIND_USER_EMAIL'),
                subscription_key=os.getenv('FORTUNAMIND_SUBSCRIPTION_KEY')
            )
            self.journal = TradingJournalManager(self.client)
            
            # Validate credentials
            validation = await self.client.validate_subscription()
            if validation.get('valid', False):
                self.initialized = True
                logger.info("FortunaMind Persistent MCP initialized successfully")
            else:
                logger.error(f"Invalid subscription: {validation.get('error', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Failed to initialize persistent client: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.close()


# Global wrapper instance
wrapper = FortunaMindMCPWrapper()


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools for Claude Desktop"""
    
    if not wrapper.initialized:
        await wrapper.initialize()
    
    tools = [
        Tool(
            name="store_journal_entry",
            description="""
            Store a trading journal entry with persistent storage.
            
            This tool allows you to save trading thoughts, analysis, reflections,
            and other journal entries that persist across sessions.
            
            The entry will be stored with your user identity and can be retrieved later.
            Supports different entry types and tags for organization.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "entry": {
                        "type": "string",
                        "description": "The journal entry content"
                    },
                    "entry_type": {
                        "type": "string", 
                        "description": "Type of entry: trade, analysis, reflection, idea, research, etc.",
                        "default": "general"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for categorization (e.g., BTC, analysis, strategy_name)"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata (symbol, price, confidence, etc.)",
                        "additionalProperties": True
                    }
                },
                "required": ["entry"]
            }
        ),
        Tool(
            name="get_journal_entries",
            description="""
            Retrieve your stored journal entries with filtering options.
            
            Returns entries in reverse chronological order (newest first).
            Supports filtering by entry type and pagination.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of entries to return",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "offset": {
                        "type": "integer", 
                        "description": "Number of entries to skip (for pagination)",
                        "default": 0,
                        "minimum": 0
                    },
                    "entry_type": {
                        "type": "string",
                        "description": "Filter by entry type (trade, analysis, reflection, etc.)"
                    }
                }
            }
        ),
        Tool(
            name="log_trade_entry",
            description="""
            Log a trading transaction with structured metadata.
            
            This is a specialized tool for logging actual trades with
            consistent formatting and metadata structure.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading pair symbol (e.g., BTC-USD, ETH-USD)"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["buy", "sell"],
                        "description": "Trade action: buy or sell"
                    },
                    "quantity": {
                        "type": "number",
                        "description": "Quantity traded"
                    },
                    "price": {
                        "type": "number", 
                        "description": "Trade price"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Reasoning behind the trade decision"
                    },
                    "strategy": {
                        "type": "string",
                        "description": "Trading strategy used (optional)"
                    }
                },
                "required": ["symbol", "action", "quantity", "price", "reasoning"]
            }
        ),
        Tool(
            name="log_analysis_entry",
            description="""
            Log market analysis with structured outlook and confidence.
            
            Use this tool to store your market analysis with consistent
            formatting for future reference and performance tracking.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Symbol being analyzed"
                    },
                    "analysis": {
                        "type": "string",
                        "description": "Your market analysis content"
                    },
                    "outlook": {
                        "type": "string",
                        "enum": ["bullish", "bearish", "neutral"],
                        "description": "Market outlook"
                    },
                    "confidence": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "description": "Confidence level in your analysis (1-10)"
                    }
                },
                "required": ["symbol", "analysis"]
            }
        ),
        Tool(
            name="get_user_stats",
            description="""
            Get your usage statistics and subscription information.
            
            Returns information about your journal usage, subscription tier,
            and other account metrics.
            """,
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_entries_by_symbol",
            description="""
            Search for journal entries related to a specific trading symbol.
            
            This tool filters through your journal entries to find all
            entries related to a particular symbol or coin.
            """,
            inputSchema={
                "type": "object", 
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol to search for (e.g., BTC, ETH, BTC-USD)"
                    },
                    "entry_type": {
                        "type": "string",
                        "description": "Optionally filter by entry type"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum entries to return"
                    }
                },
                "required": ["symbol"]
            }
        )
    ]
    
    return tools


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any] | None) -> List[TextContent]:
    """Handle tool calls from Claude Desktop"""
    
    if not wrapper.initialized:
        await wrapper.initialize()
        
    if not wrapper.initialized:
        return [TextContent(
            type="text",
            text="❌ FortunaMind Persistent MCP not initialized. Please check your credentials."
        )]
    
    try:
        if name == "store_journal_entry":
            entry = arguments.get("entry", "")
            entry_type = arguments.get("entry_type", "general")
            tags = arguments.get("tags", [])
            metadata = arguments.get("metadata", {})
            
            result = await wrapper.client.store_journal_entry(
                entry=entry,
                entry_type=entry_type,
                tags=tags,
                metadata=metadata
            )
            
            if result.get("success"):
                return [TextContent(
                    type="text",
                    text=f"✅ Journal entry stored successfully!\n\nEntry ID: {result.get('entry_id')}\nType: {entry_type}\nTags: {', '.join(tags) if tags else 'None'}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to store journal entry: {result.get('error', 'Unknown error')}"
                )]
        
        elif name == "get_journal_entries":
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            entry_type = arguments.get("entry_type")
            
            result = await wrapper.client.get_journal_entries(
                limit=limit,
                offset=offset,
                entry_type=entry_type
            )
            
            if result.get("success"):
                entries = result.get("entries", [])
                
                if not entries:
                    return [TextContent(
                        type="text",
                        text="📝 No journal entries found matching your criteria."
                    )]
                
                # Format entries for display
                formatted_entries = []
                for i, entry in enumerate(entries, 1):
                    metadata = entry.get("metadata", {})
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except json.JSONDecodeError:
                            metadata = {}
                    
                    entry_text = f"**Entry {i}** (ID: {entry.get('id', 'unknown')[:8]}...)\n"
                    entry_text += f"Type: {metadata.get('entry_type', 'general')}\n"
                    entry_text += f"Created: {entry.get('created_at', 'unknown')}\n"
                    
                    if metadata.get('tags'):
                        entry_text += f"Tags: {', '.join(metadata['tags'])}\n"
                    
                    entry_text += f"\n{entry.get('entry', '')}\n"
                    
                    if metadata and len(metadata) > 2:  # More than just entry_type and tags
                        entry_text += f"\nMetadata: {json.dumps({k: v for k, v in metadata.items() if k not in ['entry_type', 'tags']}, indent=2)}\n"
                    
                    entry_text += "\n" + "─" * 50 + "\n"
                    formatted_entries.append(entry_text)
                
                return [TextContent(
                    type="text",
                    text=f"📝 Retrieved {len(entries)} journal entries:\n\n" + "\n".join(formatted_entries)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to retrieve entries: {result.get('error', 'Unknown error')}"
                )]
        
        elif name == "log_trade_entry":
            symbol = arguments.get("symbol", "")
            action = arguments.get("action", "")
            quantity = arguments.get("quantity", 0)
            price = arguments.get("price", 0)
            reasoning = arguments.get("reasoning", "")
            strategy = arguments.get("strategy")
            
            result = await wrapper.journal.log_trade_entry(
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                reasoning=reasoning,
                strategy=strategy
            )
            
            if result.get("success"):
                trade_value = quantity * price
                return [TextContent(
                    type="text",
                    text=f"✅ Trade logged successfully!\n\n"
                          f"📊 **Trade Details:**\n"
                          f"• Symbol: {symbol}\n"
                          f"• Action: {action.upper()}\n"
                          f"• Quantity: {quantity}\n"
                          f"• Price: ${price:,.2f}\n"
                          f"• Total Value: ${trade_value:,.2f}\n"
                          f"• Strategy: {strategy or 'Not specified'}\n\n"
                          f"📝 **Reasoning:** {reasoning}\n\n"
                          f"Entry ID: {result.get('entry_id')}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to log trade: {result.get('error', 'Unknown error')}"
                )]
        
        elif name == "log_analysis_entry":
            symbol = arguments.get("symbol", "")
            analysis = arguments.get("analysis", "")
            outlook = arguments.get("outlook")
            confidence = arguments.get("confidence")
            
            result = await wrapper.journal.log_analysis_entry(
                symbol=symbol,
                analysis=analysis,
                outlook=outlook,
                confidence=confidence
            )
            
            if result.get("success"):
                return [TextContent(
                    type="text",
                    text=f"✅ Analysis logged successfully!\n\n"
                          f"📈 **Analysis for {symbol}:**\n"
                          f"{analysis}\n\n"
                          f"• Outlook: {outlook.capitalize() if outlook else 'Not specified'}\n"
                          f"• Confidence: {confidence}/10\n" if confidence else "• Confidence: Not specified\n"
                          f"\nEntry ID: {result.get('entry_id')}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to log analysis: {result.get('error', 'Unknown error')}"
                )]
        
        elif name == "get_user_stats":
            result = await wrapper.client.get_user_stats()
            
            if result.get("success"):
                stats = result
                return [TextContent(
                    type="text",
                    text=f"📊 **Your FortunaMind Statistics:**\n\n"
                          f"• Total Entries: {stats.get('total_entries', 'Unknown')}\n"
                          f"• This Month: {stats.get('entries_this_month', 'Unknown')}\n" 
                          f"• Subscription Tier: {stats.get('tier', 'Unknown')}\n"
                          f"• Account Status: {stats.get('status', 'Unknown')}\n\n"
                          f"Recent activity looks good! 📈"
                )]
            else:
                return [TextContent(
                    type="text", 
                    text=f"❌ Failed to get stats: {result.get('error', 'Unknown error')}"
                )]
        
        elif name == "search_entries_by_symbol":
            symbol = arguments.get("symbol", "").upper()
            entry_type = arguments.get("entry_type")
            limit = arguments.get("limit", 50)
            
            # Get all entries and filter client-side (since server doesn't support symbol search yet)
            result = await wrapper.client.get_journal_entries(
                limit=limit,
                entry_type=entry_type
            )
            
            if result.get("success"):
                all_entries = result.get("entries", [])
                
                # Filter by symbol
                matching_entries = []
                for entry in all_entries:
                    metadata = entry.get("metadata", {})
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except json.JSONDecodeError:
                            metadata = {}
                    
                    # Check if symbol appears in metadata, tags, or entry text
                    entry_text = entry.get("entry", "").upper()
                    entry_symbol = metadata.get("symbol", "").upper()
                    entry_tags = [tag.upper() for tag in metadata.get("tags", [])]
                    
                    if (symbol in entry_text or 
                        symbol == entry_symbol or 
                        symbol in entry_tags or
                        any(symbol in tag for tag in entry_tags)):
                        matching_entries.append(entry)
                
                if not matching_entries:
                    return [TextContent(
                        type="text",
                        text=f"🔍 No entries found for symbol '{symbol}'"
                    )]
                
                # Format results
                formatted_entries = []
                for i, entry in enumerate(matching_entries[:20], 1):  # Limit display to 20
                    metadata = entry.get("metadata", {})
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except json.JSONDecodeError:
                            metadata = {}
                    
                    entry_text = f"**Entry {i}** - {metadata.get('entry_type', 'general').title()}\n"
                    entry_text += f"Date: {entry.get('created_at', 'unknown')}\n"
                    
                    # Show key metadata
                    if metadata.get("price"):
                        entry_text += f"Price: ${metadata['price']:,.2f}\n"
                    if metadata.get("action"):
                        entry_text += f"Action: {metadata['action'].upper()}\n"
                    if metadata.get("outlook"):
                        entry_text += f"Outlook: {metadata['outlook'].capitalize()}\n"
                    
                    entry_text += f"\n{entry.get('entry', '')[:200]}...\n"
                    entry_text += "\n" + "─" * 40 + "\n"
                    formatted_entries.append(entry_text)
                
                return [TextContent(
                    type="text",
                    text=f"🔍 Found {len(matching_entries)} entries for **{symbol}**:\n\n" + 
                          "\n".join(formatted_entries[:10]) +  # Show first 10
                          (f"\n... and {len(matching_entries) - 10} more entries" if len(matching_entries) > 10 else "")
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to search entries: {result.get('error', 'Unknown error')}"
                )]
        
        else:
            return [TextContent(
                type="text",
                text=f"❌ Unknown tool: {name}"
            )]
    
    except Exception as e:
        logger.error(f"Tool execution error: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"❌ Error executing {name}: {str(e)}"
        )]


async def main():
    """Run the MCP server for Claude Desktop integration"""
    logger.info("Starting FortunaMind Persistent MCP Server for Claude Desktop")
    
    # Check for required environment variables
    if not os.getenv('FORTUNAMIND_USER_EMAIL') or not os.getenv('FORTUNAMIND_SUBSCRIPTION_KEY'):
        logger.error("""
Missing required environment variables:
- FORTUNAMIND_USER_EMAIL: Your email address
- FORTUNAMIND_SUBSCRIPTION_KEY: Your subscription key (fm_sub_xxx format)

Set these in your Claude Desktop MCP configuration.
        """)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="fortunamind-persistent",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())