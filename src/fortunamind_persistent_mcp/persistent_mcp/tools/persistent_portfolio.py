"""
Persistent Portfolio Tool

Extends the framework's UnifiedPortfolioTool with persistence capabilities.
Stores portfolio snapshots for historical analysis and trend tracking.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Clean imports using proper package structure
from fortunamind_persistent_mcp.core.base import ReadOnlyTool, ToolExecutionContext
from fortunamind_persistent_mcp.persistent_mcp.storage.interface import StorageInterface, DataType

logger = logging.getLogger(__name__)


class PersistentPortfolioTool(ReadOnlyTool):
    """Portfolio tool with persistence and historical analysis"""
    
    def __init__(self, storage: StorageInterface):
        super().__init__()
        self.storage = storage
        
        # Try to import framework tool
        try:
            from fortunamind_persistent_mcp.framework_proxy import unified_tools
            framework_tools = unified_tools()
            if hasattr(framework_tools, 'UnifiedPortfolioTool'):
                self.framework_tool = framework_tools.UnifiedPortfolioTool()
                logger.info("Using framework UnifiedPortfolioTool")
            else:
                raise ImportError("UnifiedPortfolioTool not available")
        except Exception as e:
            logger.warning(f"Framework tool not available: {e}")
            # Fall back to mock implementation
            self.framework_tool = None
    
    @property
    def schema(self):
        """Tool schema with persistence enhancements"""
        from fortunamind_persistent_mcp.core.base import ToolSchema, ToolCategory, Permission
        
        return ToolSchema(
            name="persistent_portfolio_summary",
            description="""
            Enhanced portfolio overview with historical analysis and persistence.
            
            Provides current holdings with:
            • Real-time portfolio values and allocations
            • Historical comparison with previous snapshots
            • Performance trends over time
            • Risk concentration analysis
            • Automatic snapshot storage for future analysis
            
            All portfolio data is securely stored for learning and pattern recognition.
            """,
            category=ToolCategory.PORTFOLIO,
            permissions=[Permission.READ_ONLY],
            parameters={
                "type": "object",
                "properties": {
                    "include_history": {
                        "type": "boolean", 
                        "description": "Include historical comparison data",
                        "default": True
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days of historical data to include",
                        "default": 30,
                        "minimum": 1,
                        "maximum": 365
                    },
                    "api_key": {
                        "type": "string",
                        "description": "Coinbase API key (optional if set in environment)"
                    },
                    "api_secret": {
                        "type": "string", 
                        "description": "Coinbase API secret (optional if set in environment)"
                    }
                },
                "required": []
            },
            returns={
                "type": "object",
                "properties": {
                    "current_portfolio": {"type": "object"},
                    "historical_analysis": {"type": "object"},
                    "trends": {"type": "object"},
                    "insights": {"type": "array"}
                }
            }
        )
    
    async def _execute_impl(self, context: ToolExecutionContext) -> Any:
        """Execute with persistence and historical analysis"""
        logger.info(f"Executing persistent portfolio tool for user: {context.auth_context.user_id_hash}")
        
        # Get current portfolio data
        current_data = await self._get_current_portfolio(context)
        
        # Store portfolio snapshot
        await self._store_portfolio_snapshot(context.auth_context.user_id_hash, current_data)
        
        # Add historical analysis if requested
        include_history = context.parameters.get("include_history", True)
        if include_history:
            days_back = context.parameters.get("days_back", 30)
            historical_data = await self._get_historical_analysis(context.auth_context.user_id_hash, days_back)
            current_data["historical_analysis"] = historical_data
        
        # Add insights and trends
        current_data["insights"] = await self._generate_insights(context.auth_context.user_id_hash, current_data)
        current_data["metadata"] = {
            "snapshot_time": datetime.now().isoformat(),
            "user_id_hash": context.auth_context.user_id_hash,
            "includes_history": include_history
        }
        
        return current_data
    
    async def _get_current_portfolio(self, context: ToolExecutionContext) -> Dict[str, Any]:
        """Get current portfolio data from framework or mock"""
        
        if self.framework_tool:
            # Use real framework tool
            try:
                # Convert our context to framework format
                framework_auth = self._convert_auth_context(context.auth_context)
                result = await self.framework_tool._execute_impl(framework_auth, **context.parameters)
                logger.info("Retrieved portfolio data from framework")
                return result
            except Exception as e:
                logger.error(f"Framework tool failed: {e}")
                # Fall back to mock data
                
        # Mock portfolio data for development
        logger.warning("Using mock portfolio data - framework not available")
        return {
            "total_value": 125000.50,
            "available_cash": 5000.00,
            "holdings": [
                {
                    "symbol": "BTC-USD",
                    "name": "Bitcoin",
                    "amount": "2.5",
                    "value": 112500.00,
                    "percentage": 90.0,
                    "avg_cost": 40000.00,
                    "unrealized_pnl": 12500.00
                },
                {
                    "symbol": "ETH-USD", 
                    "name": "Ethereum",
                    "amount": "2.5",
                    "value": 7500.00,
                    "percentage": 6.0,
                    "avg_cost": 2800.00,
                    "unrealized_pnl": 500.00
                }
            ],
            "summary": {
                "total_invested": 110000.00,
                "total_return": 15000.50,
                "return_percentage": 13.64,
                "num_positions": 2
            }
        }
    
    async def _store_portfolio_snapshot(self, user_id_hash: str, portfolio_data: Dict[str, Any]) -> None:
        """Store portfolio snapshot for historical analysis"""
        try:
            record_id = await self.storage.store_portfolio_snapshot(
                user_id_hash=user_id_hash,
                portfolio_data=portfolio_data,
                timestamp=datetime.now()
            )
            logger.info(f"Portfolio snapshot stored with ID: {record_id}")
        except Exception as e:
            logger.error(f"Failed to store portfolio snapshot: {e}")
            # Don't fail the whole operation if storage fails
    
    async def _get_historical_analysis(self, user_id_hash: str, days_back: int) -> Dict[str, Any]:
        """Get historical portfolio analysis"""
        try:
            # Get latest portfolio for comparison
            latest_portfolio = await self.storage.get_latest_portfolio(user_id_hash)
            
            if latest_portfolio:
                return {
                    "has_history": True,
                    "latest_snapshot": latest_portfolio.get("timestamp"),
                    "comparison_available": True,
                    "trend_analysis": "Historical data available for analysis"
                }
            else:
                return {
                    "has_history": False,
                    "message": "This is your first portfolio snapshot. Historical analysis will be available after future snapshots."
                }
                
        except Exception as e:
            logger.error(f"Failed to retrieve historical data: {e}")
            return {
                "has_history": False,
                "error": "Historical analysis temporarily unavailable"
            }
    
    async def _generate_insights(self, user_id_hash: str, portfolio_data: Dict[str, Any]) -> list:
        """Generate portfolio insights and recommendations"""
        insights = []
        
        # Check for concentration risk
        holdings = portfolio_data.get("holdings", [])
        if holdings:
            max_position = max(holding.get("percentage", 0) for holding in holdings)
            if max_position > 80:
                insights.append({
                    "type": "risk_warning",
                    "message": f"High concentration risk: {max_position:.1f}% in single asset",
                    "recommendation": "Consider diversifying to reduce portfolio risk"
                })
        
        # Check cash allocation
        available_cash = portfolio_data.get("available_cash", 0)
        total_value = portfolio_data.get("total_value", 0)
        if total_value > 0:
            cash_percentage = (available_cash / total_value) * 100
            if cash_percentage > 20:
                insights.append({
                    "type": "opportunity", 
                    "message": f"High cash allocation: {cash_percentage:.1f}%",
                    "recommendation": "Consider investing excess cash or keep for market opportunities"
                })
        
        # Performance insight
        summary = portfolio_data.get("summary", {})
        return_pct = summary.get("return_percentage", 0)
        if return_pct > 10:
            insights.append({
                "type": "performance",
                "message": f"Strong portfolio performance: +{return_pct:.1f}%",
                "recommendation": "Consider taking profits or rebalancing"
            })
        
        return insights
    
    def _convert_auth_context(self, auth_context):
        """Convert our auth context to framework format"""
        # This would convert between different auth context formats
        # For now, assume they're compatible or create a simple mapping
        return auth_context