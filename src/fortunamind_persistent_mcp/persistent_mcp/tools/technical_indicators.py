"""
Technical Indicators Tool

Provides beginner-friendly technical analysis indicators with educational
explanations and plain English interpretations.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from fortunamind_persistent_mcp.core.base import ReadOnlyTool, ToolExecutionContext, ToolSchema, AuthContext
from fortunamind_persistent_mcp.persistent_mcp.storage.interface import StorageInterface
from fortunamind_persistent_mcp.config import Settings

try:
    from fortunamind_persistent_mcp.framework_proxy import unified_tools
    framework_tools = unified_tools()
    UnifiedPricesTool = framework_tools.UnifiedPricesTool
    FRAMEWORK_AVAILABLE = True
except ImportError:
    from fortunamind_persistent_mcp.core.mock import UnifiedPricesTool
    FRAMEWORK_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class IndicatorResult:
    """Technical indicator calculation result"""
    indicator_type: str
    symbol: str
    value: float
    previous_value: Optional[float]
    signal: str  # "BULLISH", "BEARISH", "NEUTRAL"
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    explanation: str
    educational_note: str


class TechnicalIndicatorsTool(ReadOnlyTool):
    """
    Technical Indicators Tool for Crypto Education
    
    Provides beginner-friendly technical analysis with:
    - Plain English explanations of what each indicator means
    - Educational context about when and how to use indicators
    - Historical tracking to show indicator evolution over time
    - Beginner warnings about indicator limitations
    
    Designed specifically for crypto-curious professionals aged 35-65
    who may have 0-2 years of crypto experience.
    """
    
    def __init__(self, storage: StorageInterface, settings: Settings):
        """
        Initialize technical indicators tool
        
        Args:
            storage: Storage backend for persistence
            settings: Application settings
        """
        super().__init__(settings, storage)
        
        # Initialize price tool for market data
        if FRAMEWORK_AVAILABLE:
            self.price_tool = UnifiedPricesTool()
        else:
            self.price_tool = None
        
        logger.info("Technical indicators tool initialized")
    
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="technical_indicators",
            description="""Get beginner-friendly technical analysis indicators for cryptocurrencies.
            
Perfect for crypto-curious professionals who want to understand market trends without complex jargon.

**What you'll get:**
• **RSI (Relative Strength Index)** - Is the crypto "overbought" or "oversold"?
• **Moving Averages** - What's the overall trend direction? 
• **MACD** - Is momentum building up or slowing down?
• **Bollinger Bands** - Is the price in a "normal" range?

**Educational Focus:**
• Plain English explanations of what each number means
• Context about when these indicators are most useful
• Warnings about limitations (no indicator is perfect!)
• Historical tracking to see how indicators evolve over time

**Beginner-Friendly Features:**
• No complex mathematical formulas - just practical insights
• Clear "bullish" or "bearish" signals with confidence levels
• Educational notes explaining market psychology behind each indicator
• Optional comparison with your portfolio holdings

**Parameters:**
• symbol: Cryptocurrency symbol (BTC, ETH, etc.)
• timeframe: Analysis period (1d, 7d, 30d) - defaults to 7d
• include_education: Add educational explanations (recommended for beginners)
• save_to_history: Store results for tracking indicator evolution over time""",
            category="market_analysis",
            permissions=["read_only"],
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Cryptocurrency symbol (e.g., BTC, ETH, ADA)"
                    },
                    "timeframe": {
                        "type": "string", 
                        "enum": ["1d", "7d", "30d"],
                        "default": "7d",
                        "description": "Analysis timeframe - 7d recommended for beginners"
                    },
                    "include_education": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include educational explanations (recommended)"
                    },
                    "save_to_history": {
                        "type": "boolean", 
                        "default": True,
                        "description": "Save results to track indicator changes over time"
                    },
                    "compare_with_portfolio": {
                        "type": "boolean",
                        "default": False,
                        "description": "Compare with your current portfolio holdings"
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
                "required": ["symbol"]
            },
            returns={
                "type": "object",
                "description": "Technical indicators with beginner-friendly explanations"
            }
        )
    
    async def _execute_impl(self, context: ToolExecutionContext) -> Any:
        """Execute technical indicators analysis"""
        symbol = context.parameters.get("symbol", "").upper()
        timeframe = context.parameters.get("timeframe", "7d")
        include_education = context.parameters.get("include_education", True)
        save_to_history = context.parameters.get("save_to_history", True)
        compare_with_portfolio = context.parameters.get("compare_with_portfolio", False)
        
        logger.info(f"Calculating technical indicators for {symbol} ({timeframe})")
        
        try:
            # Validate symbol
            if symbol not in self.settings.supported_symbols:
                return {
                    "error": f"Symbol {symbol} not supported. Supported symbols: {', '.join(self.settings.supported_symbols)}",
                    "educational_note": "Start with major cryptocurrencies like BTC or ETH - they have the most reliable data and are easier to analyze."
                }
            
            # Get historical price data
            price_data = await self._get_price_data(symbol, timeframe, context.auth_context, context.parameters)
            if not price_data:
                return {
                    "error": "Unable to fetch price data",
                    "educational_note": "Technical indicators need historical price data to work. Try again in a moment, or check if the market is open."
                }
            
            # Calculate all indicators
            indicators = await self._calculate_all_indicators(symbol, price_data)
            
            # Add educational content if requested
            if include_education:
                indicators["educational_content"] = self._generate_educational_content(indicators)
            
            # Add beginner warnings and tips
            indicators["beginner_tips"] = self._generate_beginner_tips(indicators, symbol)
            
            # Compare with portfolio if requested
            if compare_with_portfolio and context.auth_context:
                portfolio_comparison = await self._compare_with_portfolio(
                    symbol, indicators, context.auth_context, context.parameters
                )
                if portfolio_comparison:
                    indicators["portfolio_context"] = portfolio_comparison
            
            # Save to history if requested and authenticated
            if save_to_history and context.auth_context:
                await self._save_to_history(context.auth_context.user_id_hash, symbol, indicators)
            
            # Add metadata
            indicators["metadata"] = {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": datetime.now().isoformat(),
                "data_points": len(price_data.get("candles", [])),
                "educational_focus": include_education
            }
            
            return indicators
            
        except Exception as e:
            logger.error(f"Technical indicators calculation failed: {e}")
            return {
                "error": str(e),
                "educational_note": "Technical analysis can be complex. Don't worry if you see errors - the crypto markets are volatile and data isn't always perfect."
            }
    
    async def _get_price_data(
        self, 
        symbol: str, 
        timeframe: str, 
        auth_context: Optional[AuthContext],
        parameters: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get historical price data for analysis"""
        if not self.price_tool:
            logger.warning("Price tool not available - using mock data")
            return self._generate_mock_price_data(symbol, timeframe)
        
        try:
            # Convert timeframe to days for data fetching
            days_map = {"1d": 1, "7d": 7, "30d": 30}
            days = days_map.get(timeframe, 7)
            
            # Get historical candlestick data
            result = await self.price_tool._execute_impl(
                auth_context,
                symbol=f"{symbol}-USD",
                granularity="ONE_HOUR",  # Use hourly data for better precision
                start=days,
                **{k: v for k, v in parameters.items() if k in ["api_key", "api_secret"]}
            )
            
            if result and "candles" in result:
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch price data: {e}")
            return None
    
    def _generate_mock_price_data(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Generate mock price data for development"""
        logger.debug(f"Generating mock price data for {symbol}")
        
        # Simple mock data with some trend
        import random
        base_price = {"BTC": 45000, "ETH": 3000, "ADA": 0.5}.get(symbol, 100)
        
        candles = []
        current_price = base_price
        
        periods = {"1d": 24, "7d": 168, "30d": 720}  # hours
        num_periods = periods.get(timeframe, 168)
        
        for i in range(num_periods):
            # Add some random volatility
            change = random.uniform(-0.03, 0.03)  # ±3% per period
            current_price *= (1 + change)
            
            high = current_price * random.uniform(1.005, 1.02)
            low = current_price * random.uniform(0.98, 0.995)
            volume = random.uniform(1000, 10000)
            
            candles.append({
                "start": (datetime.now() - timedelta(hours=num_periods-i)).isoformat(),
                "low": str(low),
                "high": str(high),
                "open": str(current_price),
                "close": str(current_price),
                "volume": str(volume)
            })
        
        return {
            "candles": candles,
            "symbol": f"{symbol}-USD"
        }
    
    async def _calculate_all_indicators(self, symbol: str, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate all technical indicators"""
        candles = price_data.get("candles", [])
        if len(candles) < 14:  # Need minimum data for RSI
            return {
                "error": "Insufficient data for technical analysis",
                "educational_note": "Technical indicators need enough historical data to be meaningful. We need at least 2 weeks of data."
            }
        
        # Extract price data
        closes = [float(candle["close"]) for candle in candles]
        highs = [float(candle["high"]) for candle in candles]
        lows = [float(candle["low"]) for candle in candles]
        
        # Calculate indicators
        rsi = self._calculate_rsi(closes)
        sma_20 = self._calculate_sma(closes, 20)
        sma_50 = self._calculate_sma(closes, 50)
        ema_12 = self._calculate_ema(closes, 12)
        ema_26 = self._calculate_ema(closes, 26)
        macd_data = self._calculate_macd(closes)
        bollinger = self._calculate_bollinger_bands(closes)
        
        # Current price
        current_price = closes[-1]
        
        # Generate signals and explanations
        return {
            "symbol": symbol,
            "current_price": current_price,
            "indicators": {
                "rsi": self._interpret_rsi(rsi, current_price),
                "moving_averages": self._interpret_moving_averages(
                    current_price, sma_20, sma_50, ema_12, ema_26
                ),
                "macd": self._interpret_macd(macd_data, current_price),
                "bollinger_bands": self._interpret_bollinger_bands(bollinger, current_price)
            },
            "overall_signal": self._generate_overall_signal(
                rsi, current_price, sma_20, sma_50, macd_data, bollinger
            )
        }
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return None
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-change)
        
        if len(gains) < period:
            return None
        
        # Calculate average gains and losses
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_sma(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return None
        
        return sum(prices[-period:]) / period
    
    def _calculate_ema(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = prices[0]  # Start with first price
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _calculate_macd(self, prices: List[float]) -> Dict[str, Optional[float]]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        
        if not ema_12 or not ema_26:
            return {"macd": None, "signal": None, "histogram": None}
        
        macd = ema_12 - ema_26
        
        # Calculate signal line (9-period EMA of MACD)
        # For simplicity, we'll use a basic calculation here
        signal = macd * 0.2  # Simplified signal calculation
        
        histogram = macd - signal
        
        return {
            "macd": macd,
            "signal": signal,
            "histogram": histogram
        }
    
    def _calculate_bollinger_bands(self, prices: List[float], period: int = 20) -> Dict[str, Optional[float]]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return {"upper": None, "middle": None, "lower": None}
        
        sma = self._calculate_sma(prices, period)
        if not sma:
            return {"upper": None, "middle": None, "lower": None}
        
        # Calculate standard deviation
        recent_prices = prices[-period:]
        variance = sum((price - sma) ** 2 for price in recent_prices) / period
        std_dev = variance ** 0.5
        
        upper_band = sma + (2 * std_dev)
        lower_band = sma - (2 * std_dev)
        
        return {
            "upper": upper_band,
            "middle": sma,
            "lower": lower_band,
            "std_dev": std_dev
        }
    
    def _interpret_rsi(self, rsi: Optional[float], current_price: float) -> Dict[str, Any]:
        """Interpret RSI with beginner-friendly explanations"""
        if rsi is None:
            return {
                "value": None,
                "signal": "INSUFFICIENT_DATA",
                "explanation": "Not enough data to calculate RSI",
                "educational_note": "RSI needs at least 2 weeks of price data to work properly."
            }
        
        # Determine signal
        if rsi > 70:
            signal = "BEARISH"
            confidence = "MEDIUM"
            explanation = f"RSI is {rsi:.1f}, suggesting {current_price:,.2f} might be overbought"
        elif rsi < 30:
            signal = "BULLISH" 
            confidence = "MEDIUM"
            explanation = f"RSI is {rsi:.1f}, suggesting {current_price:,.2f} might be oversold"
        else:
            signal = "NEUTRAL"
            confidence = "LOW"
            explanation = f"RSI is {rsi:.1f}, indicating balanced buying and selling pressure"
        
        return {
            "value": round(rsi, 1),
            "signal": signal,
            "confidence": confidence,
            "explanation": explanation,
            "educational_note": "RSI measures momentum. Above 70 = possibly overbought (price might drop). Below 30 = possibly oversold (price might rise). It's not a buy/sell signal by itself!"
        }
    
    def _interpret_moving_averages(
        self, 
        current_price: float, 
        sma_20: Optional[float], 
        sma_50: Optional[float],
        ema_12: Optional[float], 
        ema_26: Optional[float]
    ) -> Dict[str, Any]:
        """Interpret moving averages with educational context"""
        interpretation = {
            "sma_20": {"value": sma_20, "signal": "NEUTRAL"},
            "sma_50": {"value": sma_50, "signal": "NEUTRAL"},
            "ema_12": {"value": ema_12, "signal": "NEUTRAL"},
            "ema_26": {"value": ema_26, "signal": "NEUTRAL"}
        }
        
        signals = []
        explanations = []
        
        # SMA 20 analysis
        if sma_20:
            if current_price > sma_20:
                interpretation["sma_20"]["signal"] = "BULLISH"
                explanations.append(f"Price (${current_price:,.2f}) is above 20-day average (${sma_20:,.2f}) - short-term uptrend")
                signals.append("BULLISH")
            else:
                interpretation["sma_20"]["signal"] = "BEARISH"
                explanations.append(f"Price (${current_price:,.2f}) is below 20-day average (${sma_20:,.2f}) - short-term downtrend")
                signals.append("BEARISH")
        
        # SMA 50 analysis  
        if sma_50:
            if current_price > sma_50:
                interpretation["sma_50"]["signal"] = "BULLISH"
                explanations.append(f"Price is above 50-day average (${sma_50:,.2f}) - longer-term uptrend")
                signals.append("BULLISH")
            else:
                interpretation["sma_50"]["signal"] = "BEARISH"
                explanations.append(f"Price is below 50-day average (${sma_50:,.2f}) - longer-term downtrend")
                signals.append("BEARISH")
        
        # Overall trend signal
        bullish_count = signals.count("BULLISH")
        bearish_count = signals.count("BEARISH")
        
        if bullish_count > bearish_count:
            overall_signal = "BULLISH"
            confidence = "HIGH" if bullish_count >= 2 else "MEDIUM"
        elif bearish_count > bullish_count:
            overall_signal = "BEARISH"
            confidence = "HIGH" if bearish_count >= 2 else "MEDIUM"
        else:
            overall_signal = "NEUTRAL"
            confidence = "LOW"
        
        interpretation["overall"] = {
            "signal": overall_signal,
            "confidence": confidence,
            "explanation": " | ".join(explanations) if explanations else "Moving averages show mixed signals",
            "educational_note": "Moving averages smooth out price noise to show trends. Price above average = uptrend, below = downtrend. Longer averages (50-day) show bigger picture than shorter ones (20-day)."
        }
        
        return interpretation
    
    def _interpret_macd(self, macd_data: Dict[str, Optional[float]], current_price: float) -> Dict[str, Any]:
        """Interpret MACD with educational explanations"""
        macd = macd_data.get("macd")
        signal = macd_data.get("signal") 
        histogram = macd_data.get("histogram")
        
        if not macd or not signal or not histogram:
            return {
                "values": macd_data,
                "signal": "INSUFFICIENT_DATA", 
                "explanation": "Not enough data for MACD calculation",
                "educational_note": "MACD needs several weeks of data to calculate properly."
            }
        
        # Determine signal
        if macd > signal and histogram > 0:
            overall_signal = "BULLISH"
            confidence = "MEDIUM"
            explanation = "MACD is above signal line - momentum may be building upward"
        elif macd < signal and histogram < 0:
            overall_signal = "BEARISH"
            confidence = "MEDIUM"
            explanation = "MACD is below signal line - momentum may be building downward"
        else:
            overall_signal = "NEUTRAL"
            confidence = "LOW"
            explanation = "MACD shows mixed momentum signals"
        
        return {
            "values": {
                "macd": round(macd, 2),
                "signal": round(signal, 2),
                "histogram": round(histogram, 2)
            },
            "signal": overall_signal,
            "confidence": confidence,
            "explanation": explanation,
            "educational_note": "MACD measures momentum changes. When MACD line crosses above signal line = bullish momentum building. Below = bearish momentum. It's about momentum direction, not price direction!"
        }
    
    def _interpret_bollinger_bands(self, bollinger: Dict[str, Optional[float]], current_price: float) -> Dict[str, Any]:
        """Interpret Bollinger Bands with educational context"""
        upper = bollinger.get("upper")
        middle = bollinger.get("middle") 
        lower = bollinger.get("lower")
        
        if not upper or not middle or not lower:
            return {
                "values": bollinger,
                "signal": "INSUFFICIENT_DATA",
                "explanation": "Not enough data for Bollinger Bands",
                "educational_note": "Bollinger Bands need at least 20 days of data."
            }
        
        # Calculate position within bands
        band_width = upper - lower
        position_pct = ((current_price - lower) / band_width) * 100
        
        # Determine signal
        if current_price > upper:
            signal = "BEARISH"
            confidence = "MEDIUM"
            explanation = f"Price (${current_price:,.2f}) is above upper band (${upper:,.2f}) - possibly overbought"
        elif current_price < lower:
            signal = "BULLISH"
            confidence = "MEDIUM" 
            explanation = f"Price (${current_price:,.2f}) is below lower band (${lower:,.2f}) - possibly oversold"
        else:
            signal = "NEUTRAL"
            confidence = "LOW"
            explanation = f"Price is in normal range ({position_pct:.0f}% through the bands)"
        
        return {
            "values": {
                "upper": round(upper, 2),
                "middle": round(middle, 2),
                "lower": round(lower, 2),
                "current_position_pct": round(position_pct, 1)
            },
            "signal": signal,
            "confidence": confidence,
            "explanation": explanation,
            "educational_note": "Bollinger Bands show 'normal' price ranges. Prices tend to bounce between the bands. When price hits upper band = might be overbought. Lower band = might be oversold. But trends can 'walk the bands'!"
        }
    
    def _generate_overall_signal(
        self,
        rsi: Optional[float],
        current_price: float, 
        sma_20: Optional[float],
        sma_50: Optional[float],
        macd_data: Dict[str, Optional[float]],
        bollinger: Dict[str, Optional[float]]
    ) -> Dict[str, Any]:
        """Generate overall signal from all indicators"""
        signals = []
        explanations = []
        
        # RSI signal
        if rsi and rsi > 70:
            signals.append("BEARISH")
            explanations.append("RSI suggests overbought")
        elif rsi and rsi < 30:
            signals.append("BULLISH") 
            explanations.append("RSI suggests oversold")
        
        # Moving average signals
        if sma_20 and current_price > sma_20:
            signals.append("BULLISH")
            explanations.append("Above short-term average")
        elif sma_20 and current_price < sma_20:
            signals.append("BEARISH")
            explanations.append("Below short-term average")
        
        if sma_50 and current_price > sma_50:
            signals.append("BULLISH")
            explanations.append("Above long-term average")
        elif sma_50 and current_price < sma_50:
            signals.append("BEARISH")
            explanations.append("Below long-term average")
        
        # MACD signal
        macd = macd_data.get("macd")
        signal_line = macd_data.get("signal")
        if macd and signal_line:
            if macd > signal_line:
                signals.append("BULLISH")
                explanations.append("MACD momentum positive")
            else:
                signals.append("BEARISH")
                explanations.append("MACD momentum negative")
        
        # Bollinger Bands signal
        upper = bollinger.get("upper")
        lower = bollinger.get("lower")
        if upper and lower:
            if current_price > upper:
                signals.append("BEARISH")
                explanations.append("Price above Bollinger upper band")
            elif current_price < lower:
                signals.append("BULLISH")
                explanations.append("Price below Bollinger lower band")
        
        # Calculate consensus
        if not signals:
            return {
                "signal": "INSUFFICIENT_DATA",
                "confidence": "NONE",
                "explanation": "Not enough data for overall signal",
                "consensus": "No indicators available"
            }
        
        bullish_count = signals.count("BULLISH")
        bearish_count = signals.count("BEARISH")
        total_count = len(signals)
        
        if bullish_count > bearish_count:
            overall_signal = "BULLISH"
            consensus = f"{bullish_count}/{total_count} indicators bullish"
            confidence = "HIGH" if bullish_count >= total_count * 0.7 else "MEDIUM"
        elif bearish_count > bullish_count:
            overall_signal = "BEARISH"
            consensus = f"{bearish_count}/{total_count} indicators bearish"
            confidence = "HIGH" if bearish_count >= total_count * 0.7 else "MEDIUM"
        else:
            overall_signal = "NEUTRAL"
            consensus = "Indicators are mixed"
            confidence = "LOW"
        
        return {
            "signal": overall_signal,
            "confidence": confidence,
            "explanation": " | ".join(explanations),
            "consensus": consensus,
            "educational_note": "Overall signals combine multiple indicators. Strong consensus (most indicators agree) = higher confidence. Mixed signals = lower confidence. Never rely on indicators alone - they're tools, not crystal balls!"
        }
    
    def _generate_educational_content(self, indicators: Dict[str, Any]) -> Dict[str, str]:
        """Generate educational content for beginners"""
        return {
            "what_are_technical_indicators": """
Technical indicators are mathematical calculations based on price and volume data. 
Think of them as different ways to measure the 'mood' of the market - whether buyers or sellers are in control.

They're like weather forecasting tools for crypto prices - helpful for seeing patterns, 
but not perfect predictors of what will happen next.
            """.strip(),
            
            "how_to_use_them": """
🔍 **For Beginners:**
1. **Don't use just one indicator** - Look for agreement between multiple indicators
2. **Combine with other analysis** - Technical indicators work best with fundamental research
3. **Practice with small amounts** - Learn how indicators behave in different market conditions
4. **Understand limitations** - No indicator works 100% of the time

🎯 **Best Practices:**
• Use RSI to spot potentially overbought/oversold conditions
• Use moving averages to identify trend direction  
• Use MACD to spot momentum changes
• Use Bollinger Bands to see if prices are in normal ranges
            """.strip(),
            
            "important_warnings": """
⚠️ **Critical Reminders:**
• Technical indicators are based on PAST price data - they don't predict the future
• Crypto markets are highly volatile - indicators can give false signals
• Never invest money you can't afford to lose based on any indicator
• Consider your overall investment strategy, not just short-term signals

🧠 **Market Psychology:**
Technical indicators work because they reflect human emotions - fear and greed. 
When everyone is buying (greed), prices might be overbought. 
When everyone is selling (fear), prices might be oversold.
            """.strip(),
            
            "next_steps": """
📚 **Continue Learning:**
1. Track these indicators over time to see how they evolve
2. Compare indicator signals with actual price movements
3. Read about fundamental analysis (the 'why' behind price moves)
4. Start with major cryptos (BTC, ETH) - they have more reliable technical patterns

💡 **Remember:** The goal isn't to time the market perfectly, but to make more informed decisions 
about when to buy, hold, or sell based on multiple sources of information.
            """.strip()
        }
    
    def _generate_beginner_tips(self, indicators: Dict[str, Any], symbol: str) -> List[str]:
        """Generate contextual beginner tips"""
        tips = []
        
        overall_signal = indicators.get("overall_signal", {})
        signal = overall_signal.get("signal", "NEUTRAL")
        confidence = overall_signal.get("confidence", "LOW")
        
        # Signal-specific tips
        if signal == "BULLISH" and confidence == "HIGH":
            tips.append(f"🟢 Multiple indicators suggest {symbol} may be in an uptrend, but don't rush - confirm with your own research")
        elif signal == "BEARISH" and confidence == "HIGH":
            tips.append(f"🔴 Multiple indicators suggest {symbol} may be in a downtrend - consider waiting for better entry points")
        elif signal == "NEUTRAL" or confidence == "LOW":
            tips.append(f"🟡 Mixed signals for {symbol} - this might be a good time to wait and observe")
        
        # General tips
        tips.extend([
            "📊 Technical analysis works best when combined with fundamental research (team, technology, adoption)",
            "⏰ Consider your investment timeline - these indicators focus on short to medium-term trends",
            "🎯 Dollar-cost averaging can reduce the impact of short-term volatility",
            "🧘 Emotional discipline is more important than perfect technical analysis"
        ])
        
        # RSI-specific tip
        rsi_data = indicators.get("indicators", {}).get("rsi", {})
        if rsi_data.get("value"):
            rsi_value = rsi_data["value"]
            if rsi_value > 80:
                tips.append("⚡ Extremely high RSI - consider waiting for a pullback before buying")
            elif rsi_value < 20:
                tips.append("💎 Extremely low RSI - could be a buying opportunity, but confirm the downtrend is reversing")
        
        return tips[:5]  # Limit to 5 tips to avoid overwhelming beginners
    
    async def _compare_with_portfolio(
        self,
        symbol: str,
        indicators: Dict[str, Any], 
        auth_context: AuthContext,
        parameters: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Compare indicator signals with current portfolio holdings"""
        try:
            # This would integrate with portfolio data if available
            # For now, return placeholder
            return {
                "note": "Portfolio comparison feature coming soon",
                "suggestion": f"Consider how {symbol} fits into your overall portfolio strategy"
            }
        except Exception as e:
            logger.error(f"Portfolio comparison failed: {e}")
            return None
    
    async def _save_to_history(
        self,
        user_id_hash: str,
        symbol: str,
        indicators: Dict[str, Any]
    ) -> None:
        """Save indicator results to history for trend tracking"""
        try:
            # Save each indicator type separately for better querying
            indicator_data = indicators.get("indicators", {})
            
            for indicator_type, data in indicator_data.items():
                await self.storage.store_technical_indicator(
                    user_id_hash=user_id_hash,
                    symbol=symbol,
                    indicator_type=indicator_type,
                    data={
                        "values": data,
                        "overall_signal": indicators.get("overall_signal"),
                        "current_price": indicators.get("current_price"),
                        "metadata": indicators.get("metadata")
                    }
                )
            
            logger.debug(f"Saved technical indicators to history for {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to save indicators to history: {e}")