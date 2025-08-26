"""
Trading Journal Tool

Provides learning-focused trading journal with emotional pattern recognition,
decision quality scoring, and educational insights for crypto professionals.
"""

import logging
import re
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Clean imports using proper package structure
from fortunamind_persistent_mcp.core.base import WriteEnabledTool, ToolExecutionContext, ToolSchema, AuthContext, ToolCategory, Permission
from fortunamind_persistent_mcp.core.security.scanner import SecurityScanner
from fortunamind_persistent_mcp.persistent_mcp.storage.interface import StorageInterface, DataType
from fortunamind_persistent_mcp.config import Settings

logger = logging.getLogger(__name__)


class EmotionalState(str, Enum):
    """Detected emotional states in journal entries"""
    CONFIDENT = "confident"
    ANXIOUS = "anxious" 
    GREEDY = "greedy"
    FEARFUL = "fearful"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    EXCITED = "excited"
    REGRETFUL = "regretful"


class DecisionQuality(str, Enum):
    """Decision quality assessment levels"""
    EXCELLENT = "excellent"  # Well-researched, patient, disciplined
    GOOD = "good"           # Some research, reasonable timing
    AVERAGE = "average"     # Basic considerations
    POOR = "poor"          # Emotional, rushed, no research
    VERY_POOR = "very_poor" # FOMO, panic, no plan


@dataclass
class JournalInsight:
    """Generated insight from journal analysis"""
    insight_type: str
    title: str
    description: str
    recommendations: List[str]
    confidence: str


# SecurityScanner removed - now using shared SecurityScanner from core.security


class TradingJournalTool(WriteEnabledTool):
    """
    Learning-Focused Trading Journal Tool
    
    Helps crypto-curious professionals track their investment decisions,
    learn from patterns, and improve decision-making over time.
    
    Features:
    - Conversational journal entries (no complex forms)
    - Emotional pattern recognition
    - Decision quality scoring with feedback
    - Learning insights and recommendations
    - Privacy-first design (dollar amounts optional)
    - Security scanning to prevent accidental credential storage
    """
    
    def __init__(self, storage: StorageInterface, settings: Settings):
        """
        Initialize trading journal tool
        
        Args:
            storage: Storage backend for persistence
            settings: Application settings
        """
        super().__init__()
        self.storage = storage
        self.settings = settings
        self.security_scanner = SecurityScanner()
        
        logger.info("Trading journal tool initialized")
    
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="trading_journal",
            description="""Record and analyze your crypto investment decisions to improve over time.

**Perfect for learning-focused investors who want to:**
• Track what influenced their buy/sell decisions
• Identify emotional patterns that affect their choices
• Get feedback on decision quality and timing
• Learn from both wins and losses
• Build better investment discipline over time

**How it works:**
Just describe your investment decision in natural language - like talking to a friend about your trade. The system will:
• Extract key details (symbol, action, reasoning)
• Detect emotional patterns in your language
• Score your decision quality and provide feedback
• Track patterns over time to help you improve
• Protect your privacy (dollar amounts are optional)

**Security Features:**
• Automatically detects and blocks API keys or sensitive data
• Prevents prompt injection attempts
• Your data is encrypted and only accessible by you

**Entry Types:**
• **trade**: Record a buy/sell decision you made
• **analysis**: Document research or market analysis  
• **reflection**: Look back on previous decisions
• **plan**: Document investment strategy or goals
• **review**: Analyze journal patterns and get insights

Choose 'review' to see patterns in your previous entries and get personalized learning insights.""",
            category=ToolCategory.PORTFOLIO,
            permissions=[Permission.READ_ONLY, Permission.WRITE],
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add_entry", "review_entries", "get_insights", "search_entries"],
                        "description": "What you want to do with your journal"
                    },
                    "entry_type": {
                        "type": "string",
                        "enum": ["trade", "analysis", "reflection", "plan", "goal"],
                        "description": "Type of journal entry (required for add_entry)"
                    },
                    "content": {
                        "type": "string",
                        "description": "Your journal entry in natural language - describe your decision, thoughts, and reasoning"
                    },
                    "symbol": {
                        "type": "string", 
                        "description": "Cryptocurrency symbol if relevant (e.g., BTC, ETH)"
                    },
                    "trade_action": {
                        "type": "string",
                        "enum": ["buy", "sell", "hold", "research"],
                        "description": "What action you took or are considering"
                    },
                    "confidence_level": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "description": "How confident you are in this decision (1-10)"
                    },
                    "amount_usd": {
                        "type": "number",
                        "description": "Dollar amount involved (optional - helps with analysis but not required for privacy)"
                    },
                    "timeframe": {
                        "type": "string",
                        "enum": ["1d", "7d", "30d", "90d", "all"],
                        "default": "30d",
                        "description": "Time range for review/search operations"
                    },
                    "search_query": {
                        "type": "string",
                        "description": "Search term for finding specific entries"
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
                "required": ["action"]
            },
            returns={
                "type": "object",
                "description": "Journal operation result with insights and analysis"
            }
        )
    
    async def _execute_impl(self, context: ToolExecutionContext) -> Any:
        """Execute trading journal operation"""
        action = context.parameters.get("action")
        
        logger.info(f"Trading journal action: {action}")
        
        # Require authentication for all journal operations
        auth_context = self._require_auth(context.auth_context)
        
        try:
            # Route to appropriate handler
            if action == "add_entry":
                return await self._add_journal_entry(auth_context, context.parameters)
            elif action == "review_entries":
                return await self._review_entries(auth_context, context.parameters)
            elif action == "get_insights":
                return await self._get_insights(auth_context, context.parameters)
            elif action == "search_entries":
                return await self._search_entries(auth_context, context.parameters)
            else:
                return {
                    "error": f"Unknown action: {action}",
                    "supported_actions": ["add_entry", "review_entries", "get_insights", "search_entries"]
                }
                
        except Exception as e:
            logger.error(f"Trading journal operation failed: {e}")
            return {
                "error": str(e),
                "educational_note": "Sometimes journal operations can fail due to technical issues. Your data is safe - please try again."
            }
    
    async def _add_journal_entry(self, auth_context: AuthContext, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new journal entry"""
        entry_type = parameters.get("entry_type")
        content = parameters.get("content", "")
        
        if not entry_type:
            return {
                "error": "entry_type is required when adding entries",
                "supported_types": ["trade", "analysis", "reflection", "plan", "goal"]
            }
        
        if not content:
            return {
                "error": "Content is required - describe your decision, thoughts, or analysis"
            }
        
        # Security scan - additional content-specific scan since this is user-generated content
        if self._security_scanner:
            security_threats = self._security_scanner.scan_content(content, context="journal_entry")
            high_risk_threats = [
                threat for threat in security_threats
                if threat.confidence > 0.8 and threat.level.value in ['critical', 'high']
            ]
            
            if high_risk_threats:
                logger.warning(f"Security scan failed for user {auth_context.user_id_hash[:8]}...")
                return {
                    "error": "Security scan detected sensitive information",
                    "details": "Your entry contains what appears to be API keys, private keys, or other sensitive data that should not be stored in a journal.",
                    "blocked_patterns": [threat.description for threat in high_risk_threats],
                    "educational_note": "Never store API keys, passwords, or private keys in your trading journal. This protects your accounts from security breaches."
                }
        
        # Validate content length
        if len(content) > self.settings.max_journal_entry_length:
            return {
                "error": f"Entry too long. Maximum length is {self.settings.max_journal_entry_length} characters.",
                "current_length": len(content),
                "tip": "Consider breaking long entries into multiple shorter entries for better analysis."
            }
        
        # Extract information from content
        extracted_info = self._extract_entry_info(content, parameters)
        
        # Analyze emotional state
        emotional_analysis = self._analyze_emotional_state(content)
        
        # Score decision quality
        decision_quality = self._score_decision_quality(content, extracted_info, parameters)
        
        # Generate entry data
        entry_data = {
            "entry_type": entry_type,
            "content": content,
            "extracted_info": extracted_info,
            "emotional_analysis": emotional_analysis,
            "decision_quality": decision_quality,
            "metadata": {
                "symbol": parameters.get("symbol"),
                "trade_action": parameters.get("trade_action"),
                "confidence_level": parameters.get("confidence_level"),
                "amount_usd": parameters.get("amount_usd"),
                "entry_timestamp": datetime.now().isoformat(),
                "content_length": len(content),
                "word_count": len(content.split())
            },
            "tags": self._generate_tags(entry_type, extracted_info, emotional_analysis)
        }
        
        # Store entry
        entry_id = await self.storage.store_journal_entry(
            user_id_hash=auth_context.user_id_hash,
            entry_data=entry_data
        )
        
        # Generate insights for this entry
        entry_insights = self._generate_entry_insights(entry_data)
        
        logger.info(f"Added journal entry {entry_id} for user {auth_context.user_id_hash[:8]}...")
        
        return {
            "success": True,
            "entry_id": entry_id,
            "analysis": {
                "emotional_state": emotional_analysis,
                "decision_quality": decision_quality,
                "extracted_info": extracted_info
            },
            "insights": entry_insights,
            "educational_notes": self._generate_educational_feedback(entry_data),
            "next_steps": [
                "Review this entry in a few days to see how your decision played out",
                "Compare your confidence level with the actual outcome",
                "Look for emotional patterns by reviewing multiple entries",
                "Consider what additional research could improve similar future decisions"
            ]
        }
    
    async def _review_entries(self, auth_context: AuthContext, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Review previous journal entries"""
        timeframe = parameters.get("timeframe", "30d")
        
        # Calculate date range
        since = self._parse_timeframe(timeframe)
        
        # Get entries from storage
        entries = await self.storage.get_journal_entries(
            user_id_hash=auth_context.user_id_hash,
            since=since,
            limit=50
        )
        
        if not entries:
            return {
                "message": "No journal entries found in the selected timeframe",
                "suggestion": "Start by adding your first journal entry to track your investment decisions",
                "timeframe": timeframe
            }
        
        # Analyze entries
        analysis = self._analyze_entry_patterns(entries)
        
        # Generate summary
        summary = self._generate_review_summary(entries, analysis)
        
        return {
            "timeframe": timeframe,
            "entry_count": len(entries),
            "summary": summary,
            "patterns": analysis,
            "recent_entries": self._format_recent_entries(entries[:5]),  # Show 5 most recent
            "recommendations": self._generate_review_recommendations(analysis),
            "educational_insights": self._generate_learning_insights(analysis)
        }
    
    async def _get_insights(self, auth_context: AuthContext, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get personalized insights from journal analysis"""
        timeframe = parameters.get("timeframe", "90d")
        since = self._parse_timeframe(timeframe)
        
        # Get all entries for analysis
        entries = await self.storage.get_journal_entries(
            user_id_hash=auth_context.user_id_hash,
            since=since,
            limit=100
        )
        
        if len(entries) < 3:
            return {
                "message": "Need at least 3 journal entries to generate meaningful insights",
                "current_count": len(entries),
                "suggestion": "Keep journaling your decisions - insights get better with more data!"
            }
        
        # Generate comprehensive insights
        insights = self._generate_comprehensive_insights(entries)
        
        return {
            "timeframe": timeframe,
            "entries_analyzed": len(entries),
            "insights": insights,
            "improvement_areas": self._identify_improvement_areas(entries),
            "strengths": self._identify_strengths(entries),
            "action_items": self._generate_action_items(insights)
        }
    
    async def _search_entries(self, auth_context: AuthContext, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search journal entries"""
        search_query = parameters.get("search_query", "")
        timeframe = parameters.get("timeframe", "all")
        
        if not search_query:
            return {
                "error": "search_query is required",
                "examples": ["BTC", "sell decision", "anxious", "profit"]
            }
        
        since = self._parse_timeframe(timeframe) if timeframe != "all" else None
        
        # Get entries
        entries = await self.storage.get_journal_entries(
            user_id_hash=auth_context.user_id_hash,
            since=since,
            limit=100
        )
        
        # Search through entries
        matching_entries = self._search_in_entries(entries, search_query)
        
        return {
            "search_query": search_query,
            "timeframe": timeframe,
            "total_entries_searched": len(entries),
            "matching_entries": len(matching_entries),
            "results": self._format_search_results(matching_entries),
            "patterns_found": self._analyze_search_patterns(matching_entries, search_query)
        }
    
    def _extract_entry_info(self, content: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured information from journal entry content"""
        info = {
            "symbols_mentioned": [],
            "actions_mentioned": [],
            "emotions_detected": [],
            "research_mentioned": False,
            "timeframe_mentioned": None,
            "price_mentioned": False
        }
        
        # Extract cryptocurrency symbols
        crypto_patterns = [
            r'\b(BTC|Bitcoin)\b',
            r'\b(ETH|Ethereum)\b', 
            r'\b(ADA|Cardano)\b',
            r'\b(SOL|Solana)\b',
            r'\b(DOT|Polkadot)\b',
            r'\b(MATIC|Polygon)\b',
        ]
        
        for pattern in crypto_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                symbol = matches[0].upper()
                if symbol in ['BITCOIN', 'ETHEREUM', 'CARDANO', 'SOLANA', 'POLKADOT', 'POLYGON']:
                    symbol = {'BITCOIN': 'BTC', 'ETHEREUM': 'ETH', 'CARDANO': 'ADA', 'SOLANA': 'SOL', 'POLKADOT': 'DOT', 'POLYGON': 'MATIC'}[symbol]
                if symbol not in info["symbols_mentioned"]:
                    info["symbols_mentioned"].append(symbol)
        
        # Extract actions
        action_patterns = {
            "buy": [r'\b(buy|bought|purchase|purchased|accumulate|accumulating)\b'],
            "sell": [r'\b(sell|sold|selling|dump|dumping)\b'],
            "hold": [r'\b(hold|holding|hodl|hodling|keep|keeping)\b'],
            "research": [r'\b(research|researching|analyzing|studying)\b']
        }
        
        for action, patterns in action_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    info["actions_mentioned"].append(action)
                    break
        
        # Check for research indicators
        research_indicators = [
            r'\b(whitepaper|roadmap|team|partnership|adoption)\b',
            r'\b(market cap|volume|technical analysis|fundamentals)\b',
            r'\b(news|announcement|update|release)\b'
        ]
        
        for pattern in research_indicators:
            if re.search(pattern, content, re.IGNORECASE):
                info["research_mentioned"] = True
                break
        
        # Check for price/value mentions
        price_patterns = [
            r'\$[\d,]+',
            r'\b\d+k\b',
            r'\bprice\b',
            r'\bvalue\b',
            r'\bprofit\b',
            r'\bloss\b'
        ]
        
        for pattern in price_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                info["price_mentioned"] = True
                break
        
        return info
    
    def _analyze_emotional_state(self, content: str) -> Dict[str, Any]:
        """Analyze emotional state from journal content"""
        # Emotional keywords mapping
        emotion_keywords = {
            EmotionalState.CONFIDENT: [
                "confident", "sure", "certain", "convinced", "positive", "optimistic", 
                "strong conviction", "believe", "solid choice"
            ],
            EmotionalState.ANXIOUS: [
                "worried", "anxious", "nervous", "uncertain", "unsure", "concerned",
                "stressed", "tense", "uneasy"
            ],
            EmotionalState.GREEDY: [
                "moon", "lambo", "to the moon", "massive gains", "get rich", 
                "quick profit", "fomo", "don't want to miss"
            ],
            EmotionalState.FEARFUL: [
                "scared", "afraid", "panic", "fear", "terrified", "crash",
                "losing money", "disaster", "catastrophe"
            ],
            EmotionalState.FRUSTRATED: [
                "frustrated", "annoyed", "angry", "irritated", "fed up",
                "disappointed", "upset"
            ],
            EmotionalState.EXCITED: [
                "excited", "thrilled", "pumped", "enthusiastic", "amazing",
                "incredible", "fantastic"
            ],
            EmotionalState.REGRETFUL: [
                "regret", "should have", "wish I", "mistake", "wrong decision",
                "if only", "missed opportunity"
            ]
        }
        
        # Score each emotion
        emotion_scores = {}
        content_lower = content.lower()
        
        for emotion, keywords in emotion_keywords.items():
            score = 0
            found_keywords = []
            
            for keyword in keywords:
                if keyword in content_lower:
                    score += 1
                    found_keywords.append(keyword)
            
            if score > 0:
                emotion_scores[emotion.value] = {
                    "score": score,
                    "keywords_found": found_keywords
                }
        
        # Determine primary emotion
        if not emotion_scores:
            primary_emotion = EmotionalState.NEUTRAL
            confidence = "low"
        else:
            primary_emotion_key = max(emotion_scores.keys(), key=lambda k: emotion_scores[k]["score"])
            primary_emotion = EmotionalState(primary_emotion_key)
            
            max_score = emotion_scores[primary_emotion_key]["score"]
            confidence = "high" if max_score >= 3 else "medium" if max_score >= 2 else "low"
        
        return {
            "primary_emotion": primary_emotion.value,
            "confidence": confidence,
            "emotion_scores": emotion_scores,
            "emotional_intensity": self._calculate_emotional_intensity(content),
            "analysis_note": self._generate_emotional_analysis_note(primary_emotion, emotion_scores)
        }
    
    def _calculate_emotional_intensity(self, content: str) -> str:
        """Calculate overall emotional intensity of content"""
        # Look for intensity indicators
        intensity_indicators = [
            (r'[!]{2,}', 3),  # Multiple exclamation marks
            (r'[A-Z]{3,}', 2),  # ALL CAPS words
            (r'\b(extremely|incredibly|absolutely|definitely|totally)\b', 2),
            (r'\b(very|really|quite|pretty)\b', 1),
        ]
        
        total_intensity = 0
        for pattern, weight in intensity_indicators:
            matches = len(re.findall(pattern, content))
            total_intensity += matches * weight
        
        if total_intensity >= 10:
            return "very_high"
        elif total_intensity >= 6:
            return "high"
        elif total_intensity >= 3:
            return "medium"
        elif total_intensity >= 1:
            return "low"
        else:
            return "very_low"
    
    def _generate_emotional_analysis_note(self, primary_emotion: EmotionalState, emotion_scores: Dict) -> str:
        """Generate educational note about detected emotions"""
        if primary_emotion == EmotionalState.NEUTRAL:
            return "Your entry shows balanced emotional language - this often leads to better decision making."
        
        emotion_guidance = {
            EmotionalState.CONFIDENT: "Confidence is good, but make sure it's based on research, not just recent gains.",
            EmotionalState.ANXIOUS: "Anxiety is normal in volatile markets. Consider if this affects your risk tolerance.",
            EmotionalState.GREEDY: "FOMO and greed are common but dangerous. Stick to your investment plan.",
            EmotionalState.FEARFUL: "Fear can prevent good decisions and cause bad ones. Take time to think objectively.",
            EmotionalState.FRUSTRATED: "Frustration often leads to revenge trading. Step back and reassess.",
            EmotionalState.EXCITED: "Excitement is fun but can cloud judgment. Double-check your reasoning.",
            EmotionalState.REGRETFUL: "Everyone makes mistakes. Focus on learning rather than dwelling on regret."
        }
        
        return emotion_guidance.get(primary_emotion, "Monitor how emotions influence your decisions.")
    
    def _score_decision_quality(self, content: str, extracted_info: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Score the quality of the decision based on various factors"""
        score = 0
        max_score = 100
        factors = []
        
        # Research factor (0-25 points)
        if extracted_info.get("research_mentioned"):
            score += 25
            factors.append("✅ Mentioned research/analysis (+25)")
        else:
            factors.append("❌ No research mentioned (0)")
        
        # Emotional control factor (0-20 points)
        emotion_analysis = self._analyze_emotional_state(content)
        emotion = emotion_analysis.get("primary_emotion")
        
        if emotion in ["neutral", "confident"]:
            score += 20
            factors.append(f"✅ Balanced emotional state: {emotion} (+20)")
        elif emotion in ["anxious", "frustrated"]:
            score += 10
            factors.append(f"⚠️ Some emotional stress: {emotion} (+10)")
        else:
            score += 0
            factors.append(f"❌ High emotional decision: {emotion} (0)")
        
        # Planning factor (0-20 points)
        planning_indicators = [
            r'\b(plan|strategy|goal|target|timeline)\b',
            r'\b(risk|downside|upside|scenario)\b',
            r'\b(position size|allocation|portfolio)\b'
        ]
        
        planning_score = 0
        for pattern in planning_indicators:
            if re.search(pattern, content, re.IGNORECASE):
                planning_score += 7
        
        planning_score = min(planning_score, 20)
        score += planning_score
        
        if planning_score >= 15:
            factors.append("✅ Good planning mentioned (+15-20)")
        elif planning_score >= 7:
            factors.append("⚠️ Some planning mentioned (+7-14)")
        else:
            factors.append("❌ No planning mentioned (0)")
        
        # Confidence calibration (0-15 points)
        confidence_level = parameters.get("confidence_level")
        if confidence_level is not None:
            if 4 <= confidence_level <= 7:  # Moderate confidence is often better
                score += 15
                factors.append(f"✅ Well-calibrated confidence: {confidence_level}/10 (+15)")
            elif confidence_level <= 3 or confidence_level >= 9:
                score += 5
                factors.append(f"⚠️ Extreme confidence level: {confidence_level}/10 (+5)")
            else:
                score += 10
                factors.append(f"✅ Reasonable confidence: {confidence_level}/10 (+10)")
        else:
            factors.append("❓ No confidence level provided (0)")
        
        # Detail and thoughtfulness (0-20 points)
        word_count = len(content.split())
        if word_count >= 100:
            score += 20
            factors.append(f"✅ Detailed entry: {word_count} words (+20)")
        elif word_count >= 50:
            score += 15
            factors.append(f"✅ Good detail: {word_count} words (+15)")
        elif word_count >= 20:
            score += 10
            factors.append(f"⚠️ Basic detail: {word_count} words (+10)")
        else:
            score += 0
            factors.append(f"❌ Very brief: {word_count} words (0)")
        
        # Convert to quality level
        if score >= 80:
            quality = DecisionQuality.EXCELLENT
        elif score >= 65:
            quality = DecisionQuality.GOOD
        elif score >= 45:
            quality = DecisionQuality.AVERAGE
        elif score >= 25:
            quality = DecisionQuality.POOR
        else:
            quality = DecisionQuality.VERY_POOR
        
        return {
            "score": score,
            "max_score": max_score,
            "percentage": round((score / max_score) * 100, 1),
            "quality_level": quality.value,
            "factors": factors,
            "improvement_suggestions": self._generate_quality_improvements(score, factors)
        }
    
    def _generate_quality_improvements(self, score: int, factors: List[str]) -> List[str]:
        """Generate suggestions for improving decision quality"""
        suggestions = []
        
        if "❌ No research mentioned" in " ".join(factors):
            suggestions.append("📚 Document your research: What sources did you consult? What fundamentals did you consider?")
        
        if "❌ High emotional decision" in " ".join(factors):
            suggestions.append("🧘 Wait 24 hours before emotional decisions. Ask: 'Would I make this decision if the price was stable?'")
        
        if "❌ No planning mentioned" in " ".join(factors):
            suggestions.append("📋 Include your plan: What's your target price? Risk tolerance? Position size reasoning?")
        
        if "❌ Very brief" in " ".join(factors):
            suggestions.append("✍️ Write more detail: Explain your thinking process, not just the decision.")
        
        if score < 50:
            suggestions.append("🎯 Focus on process over outcome: Good decisions can have bad short-term results, and vice versa.")
        
        return suggestions[:3]  # Limit to top 3 suggestions
    
    def _generate_tags(self, entry_type: str, extracted_info: Dict[str, Any], emotional_analysis: Dict[str, Any]) -> List[str]:
        """Generate tags for the journal entry"""
        tags = [entry_type]
        
        # Add symbol tags
        for symbol in extracted_info.get("symbols_mentioned", []):
            tags.append(symbol.lower())
        
        # Add action tags
        for action in extracted_info.get("actions_mentioned", []):
            tags.append(action)
        
        # Add emotional tag
        primary_emotion = emotional_analysis.get("primary_emotion")
        if primary_emotion and primary_emotion != "neutral":
            tags.append(primary_emotion)
        
        # Add quality tags
        if extracted_info.get("research_mentioned"):
            tags.append("research")
        
        if extracted_info.get("price_mentioned"):
            tags.append("price_focused")
        
        return list(set(tags))  # Remove duplicates
    
    def _generate_entry_insights(self, entry_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate insights for a specific entry"""
        insights = []
        
        emotional_analysis = entry_data.get("emotional_analysis", {})
        decision_quality = entry_data.get("decision_quality", {})
        extracted_info = entry_data.get("extracted_info", {})
        
        # Emotional insight
        primary_emotion = emotional_analysis.get("primary_emotion")
        if primary_emotion not in ["neutral", "confident"]:
            insights.append({
                "type": "emotional_awareness",
                "title": f"Emotional State: {primary_emotion.title()}",
                "message": f"Your entry shows {primary_emotion} language. This emotion can influence decision quality.",
                "recommendation": "Consider revisiting this decision when you're in a more neutral emotional state."
            })
        
        # Decision quality insight
        quality_score = decision_quality.get("percentage", 0)
        if quality_score < 60:
            insights.append({
                "type": "decision_process",
                "title": "Decision Quality Could Improve",
                "message": f"This decision scored {quality_score}% on our quality assessment.",
                "recommendation": "Consider adding more research, planning details, or risk considerations to future entries."
            })
        
        # Research insight
        if not extracted_info.get("research_mentioned"):
            insights.append({
                "type": "research_reminder", 
                "title": "Research Documentation",
                "message": "This entry doesn't mention research or analysis.",
                "recommendation": "Document what research influenced your decision - it helps you learn from both wins and losses."
            })
        
        return insights
    
    def _generate_educational_feedback(self, entry_data: Dict[str, Any]) -> List[str]:
        """Generate educational feedback for the entry"""
        feedback = []
        
        decision_quality = entry_data.get("decision_quality", {})
        quality_level = decision_quality.get("quality_level", "average")
        
        # Quality-based feedback
        quality_feedback = {
            "excellent": [
                "🌟 Excellent decision process! You've documented research, managed emotions, and shown good planning.",
                "Keep tracking outcomes to see if your process consistently leads to good results."
            ],
            "good": [
                "👍 Good decision process with room for improvement.",
                "Consider adding more detail about your research or risk considerations."
            ],
            "average": [
                "📊 Average decision process - you're on the right track but can improve.",
                "Focus on documenting your research and managing emotions in future decisions."
            ],
            "poor": [
                "⚠️ This decision shows signs of emotional or rushed thinking.",
                "Consider waiting 24 hours and revisiting your reasoning before similar future decisions."
            ],
            "very_poor": [
                "🚨 This decision appears very emotional or poorly planned.",
                "Take a step back, do more research, and consider your long-term strategy."
            ]
        }
        
        feedback.extend(quality_feedback.get(quality_level, []))
        
        # General learning notes
        feedback.extend([
            "📚 Remember: Good processes lead to better outcomes over time, even if individual trades don't work out.",
            "🎯 Track how your confidence levels correlate with actual outcomes to improve calibration."
        ])
        
        return feedback
    
    def _parse_timeframe(self, timeframe: str) -> datetime:
        """Parse timeframe string to datetime"""
        now = datetime.now()
        
        timeframe_map = {
            "1d": timedelta(days=1),
            "7d": timedelta(days=7), 
            "30d": timedelta(days=30),
            "90d": timedelta(days=90)
        }
        
        delta = timeframe_map.get(timeframe, timedelta(days=30))
        return now - delta
    
    def _analyze_entry_patterns(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns across multiple journal entries"""
        if not entries:
            return {}
        
        # Emotional patterns
        emotions = []
        decision_scores = []
        symbols_mentioned = []
        entry_types = []
        
        for entry in entries:
            emotional_analysis = entry.get("emotional_analysis", {})
            if emotional_analysis.get("primary_emotion"):
                emotions.append(emotional_analysis["primary_emotion"])
            
            decision_quality = entry.get("decision_quality", {})
            if decision_quality.get("percentage"):
                decision_scores.append(decision_quality["percentage"])
            
            extracted_info = entry.get("extracted_info", {})
            symbols_mentioned.extend(extracted_info.get("symbols_mentioned", []))
            
            entry_types.append(entry.get("entry_type", "unknown"))
        
        # Calculate patterns
        patterns = {
            "emotional_patterns": self._analyze_emotional_patterns(emotions),
            "decision_quality_trend": self._analyze_decision_trend(decision_scores),
            "most_mentioned_symbols": self._count_frequency(symbols_mentioned),
            "entry_type_distribution": self._count_frequency(entry_types),
            "total_entries": len(entries),
            "date_range": self._get_date_range(entries)
        }
        
        return patterns
    
    def _analyze_emotional_patterns(self, emotions: List[str]) -> Dict[str, Any]:
        """Analyze emotional patterns in entries"""
        if not emotions:
            return {"message": "No emotional data to analyze"}
        
        emotion_counts = self._count_frequency(emotions)
        most_common = max(emotion_counts.keys(), key=lambda k: emotion_counts[k]) if emotion_counts else "neutral"
        
        return {
            "most_common_emotion": most_common,
            "emotion_distribution": emotion_counts,
            "emotional_volatility": len(set(emotions)) / len(emotions) if emotions else 0,
            "insight": self._generate_emotional_pattern_insight(emotion_counts, most_common)
        }
    
    def _analyze_decision_trend(self, scores: List[float]) -> Dict[str, Any]:
        """Analyze decision quality trend over time"""
        if not scores:
            return {"message": "No decision scores to analyze"}
        
        if len(scores) >= 5:
            # Calculate trend (simple linear regression)
            n = len(scores)
            x_vals = list(range(n))
            x_mean = sum(x_vals) / n
            y_mean = sum(scores) / n
            
            numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, scores))
            denominator = sum((x - x_mean) ** 2 for x in x_vals)
            
            slope = numerator / denominator if denominator != 0 else 0
            
            trend = "improving" if slope > 2 else "declining" if slope < -2 else "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "average_score": round(sum(scores) / len(scores), 1),
            "latest_score": scores[-1] if scores else 0,
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "trend": trend,
            "insight": self._generate_decision_trend_insight(scores, trend)
        }
    
    def _count_frequency(self, items: List[str]) -> Dict[str, int]:
        """Count frequency of items in list"""
        counts = {}
        for item in items:
            counts[item] = counts.get(item, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
    
    def _get_date_range(self, entries: List[Dict[str, Any]]) -> Dict[str, str]:
        """Get date range of entries"""
        if not entries:
            return {}
        
        timestamps = []
        for entry in entries:
            timestamp_str = entry.get("timestamp")
            if timestamp_str:
                try:
                    timestamps.append(datetime.fromisoformat(timestamp_str.replace("Z", "+00:00")))
                except:
                    continue
        
        if timestamps:
            return {
                "earliest": min(timestamps).isoformat(),
                "latest": max(timestamps).isoformat(),
                "span_days": (max(timestamps) - min(timestamps)).days
            }
        
        return {}
    
    def _generate_emotional_pattern_insight(self, emotion_counts: Dict[str, int], most_common: str) -> str:
        """Generate insight about emotional patterns"""
        total = sum(emotion_counts.values())
        most_common_pct = (emotion_counts.get(most_common, 0) / total) * 100 if total > 0 else 0
        
        if most_common_pct >= 50:
            return f"You tend to make decisions while feeling {most_common} ({most_common_pct:.0f}% of entries). Consider how this emotion affects your judgment."
        else:
            return f"Your emotional states vary, with {most_common} being most common. This emotional awareness can help you make better decisions."
    
    def _generate_decision_trend_insight(self, scores: List[float], trend: str) -> str:
        """Generate insight about decision quality trend"""
        if trend == "improving":
            return "🎯 Your decision-making process is improving over time! Keep documenting your thinking."
        elif trend == "declining":
            return "⚠️ Your decision quality scores are declining. Consider what might be affecting your process."
        elif trend == "stable":
            return "📊 Your decision quality is consistent. Look for specific areas to improve."
        else:
            return "📝 Keep journaling to establish trends in your decision-making quality."
    
    def _generate_review_summary(self, entries: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
        """Generate a summary of the journal review"""
        entry_count = len(entries)
        emotional_patterns = analysis.get("emotional_patterns", {})
        decision_trend = analysis.get("decision_quality_trend", {})
        
        most_common_emotion = emotional_patterns.get("most_common_emotion", "neutral")
        avg_score = decision_trend.get("average_score", 0)
        trend = decision_trend.get("trend", "unknown")
        
        summary = f"📊 **Journal Summary**: {entry_count} entries analyzed\n\n"
        summary += f"🧠 **Emotional Pattern**: Most decisions made while feeling {most_common_emotion}\n"
        summary += f"🎯 **Decision Quality**: Average score {avg_score}% ({trend} trend)\n"
        
        most_mentioned = analysis.get("most_mentioned_symbols", {})
        if most_mentioned:
            top_symbol = list(most_mentioned.keys())[0]
            summary += f"💰 **Focus**: Most entries about {top_symbol}\n"
        
        return summary
    
    def _format_recent_entries(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format recent entries for display"""
        formatted = []
        
        for entry in entries:
            formatted.append({
                "timestamp": entry.get("timestamp"),
                "entry_type": entry.get("entry_type"),
                "content_preview": entry.get("content", "")[:100] + "..." if len(entry.get("content", "")) > 100 else entry.get("content", ""),
                "primary_emotion": entry.get("emotional_analysis", {}).get("primary_emotion"),
                "decision_quality": entry.get("decision_quality", {}).get("quality_level"),
                "symbols": entry.get("extracted_info", {}).get("symbols_mentioned", [])
            })
        
        return formatted
    
    def _generate_review_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on journal analysis"""
        recommendations = []
        
        emotional_patterns = analysis.get("emotional_patterns", {})
        decision_trend = analysis.get("decision_quality_trend", {})
        
        most_common_emotion = emotional_patterns.get("most_common_emotion")
        if most_common_emotion in ["anxious", "fearful", "greedy"]:
            recommendations.append(f"🧘 You often make decisions while feeling {most_common_emotion}. Try waiting 24 hours before acting on these emotions.")
        
        avg_score = decision_trend.get("average_score", 0)
        if avg_score < 60:
            recommendations.append("📚 Your decision quality scores suggest more research and planning could help. Document your analysis process.")
        
        trend = decision_trend.get("trend")
        if trend == "declining":
            recommendations.append("📉 Your decision quality is declining. Review what changed in your process and consider returning to earlier methods that worked.")
        
        entry_count = analysis.get("total_entries", 0)
        if entry_count < 10:
            recommendations.append("📝 Keep journaling consistently - patterns become clearer with more entries.")
        
        return recommendations
    
    def _generate_learning_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate learning insights from journal analysis"""
        insights = []
        
        insights.extend([
            "🎯 **Track Outcomes**: Note which decisions led to good results and identify what made them successful",
            "📊 **Pattern Recognition**: Your emotional state during decisions is as important as the decision itself",
            "🔄 **Iterative Improvement**: Each journal entry is data to improve your investment process",
            "⏰ **Timing Awareness**: Note how market timing affects your emotional state and decision quality"
        ])
        
        return insights
    
    def _generate_comprehensive_insights(self, entries: List[Dict[str, Any]]) -> List[JournalInsight]:
        """Generate comprehensive insights from journal entries"""
        insights = []
        analysis = self._analyze_entry_patterns(entries)
        
        # Emotional insight
        emotional_patterns = analysis.get("emotional_patterns", {})
        if emotional_patterns:
            insights.append(JournalInsight(
                insight_type="emotional_awareness",
                title="Your Emotional Decision Patterns",
                description=f"You make {emotional_patterns.get('emotional_volatility', 0):.0%} of decisions while experiencing strong emotions",
                recommendations=[
                    "Practice the 24-hour rule for emotional decisions",
                    "Identify your emotional triggers in market volatility",
                    "Develop strategies for neutral-state decision making"
                ],
                confidence="high" if len(entries) >= 10 else "medium"
            ))
        
        # Decision quality insight
        decision_trend = analysis.get("decision_quality_trend", {})
        if decision_trend:
            insights.append(JournalInsight(
                insight_type="decision_quality",
                title="Decision-Making Process Evolution", 
                description=f"Your average decision quality score is {decision_trend.get('average_score', 0):.1f}% with a {decision_trend.get('trend', 'stable')} trend",
                recommendations=[
                    "Focus on process improvement rather than outcome optimization",
                    "Document research sources and time spent on analysis",
                    "Set specific criteria for buy/sell decisions"
                ],
                confidence="high" if decision_trend.get("trend") != "insufficient_data" else "low"
            ))
        
        return insights
    
    def _identify_improvement_areas(self, entries: List[Dict[str, Any]]) -> List[str]:
        """Identify areas for improvement based on journal analysis"""
        areas = []
        
        # Analyze common weaknesses
        low_research_count = 0
        high_emotion_count = 0
        low_detail_count = 0
        
        for entry in entries:
            if not entry.get("extracted_info", {}).get("research_mentioned"):
                low_research_count += 1
            
            emotion = entry.get("emotional_analysis", {}).get("primary_emotion")
            if emotion in ["anxious", "greedy", "fearful", "frustrated"]:
                high_emotion_count += 1
            
            word_count = entry.get("metadata", {}).get("word_count", 0)
            if word_count < 50:
                low_detail_count += 1
        
        total_entries = len(entries)
        
        if low_research_count / total_entries > 0.5:
            areas.append("📚 Research Documentation: Over half your entries don't mention research or analysis")
        
        if high_emotion_count / total_entries > 0.4:
            areas.append("🧘 Emotional Control: 40%+ of your decisions are made during high emotional states")
        
        if low_detail_count / total_entries > 0.6:
            areas.append("✍️ Entry Detail: Most entries are brief - more detail helps identify patterns")
        
        return areas
    
    def _identify_strengths(self, entries: List[Dict[str, Any]]) -> List[str]:
        """Identify strengths based on journal analysis"""
        strengths = []
        
        # Analyze positive patterns
        high_quality_count = 0
        research_count = 0
        detailed_count = 0
        
        for entry in entries:
            decision_quality = entry.get("decision_quality", {})
            if decision_quality.get("percentage", 0) >= 70:
                high_quality_count += 1
            
            if entry.get("extracted_info", {}).get("research_mentioned"):
                research_count += 1
            
            word_count = entry.get("metadata", {}).get("word_count", 0)
            if word_count >= 100:
                detailed_count += 1
        
        total_entries = len(entries)
        
        if high_quality_count / total_entries > 0.6:
            strengths.append("🌟 Consistent Quality: Over 60% of your decisions score well on our quality assessment")
        
        if research_count / total_entries > 0.5:
            strengths.append("📚 Research-Driven: You consistently document research in your decision process")
        
        if detailed_count / total_entries > 0.4:
            strengths.append("✍️ Thoughtful Analysis: You provide detailed reasoning in your journal entries")
        
        if len(entries) >= 20:
            strengths.append("📝 Consistent Journaling: You maintain regular journal entries - great for learning!")
        
        return strengths
    
    def _generate_action_items(self, insights: List[JournalInsight]) -> List[str]:
        """Generate specific action items from insights"""
        actions = []
        
        # Extract recommendations from insights
        for insight in insights:
            actions.extend(insight.recommendations[:1])  # Take top recommendation from each
        
        # Add general action items
        actions.extend([
            "📊 Track outcomes: Note actual results 1-2 weeks after each decision",
            "🎯 Set decision criteria: Define what makes a 'good' vs 'bad' decision for you",
            "📚 Create a research checklist: Standardize what you research before decisions"
        ])
        
        return actions[:5]  # Limit to 5 action items
    
    def _search_in_entries(self, entries: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Search for query in journal entries"""
        query_lower = query.lower()
        matching_entries = []
        
        for entry in entries:
            # Search in content
            if query_lower in entry.get("content", "").lower():
                matching_entries.append(entry)
                continue
            
            # Search in extracted info
            extracted_info = entry.get("extracted_info", {})
            if query_lower in str(extracted_info.get("symbols_mentioned", [])).lower():
                matching_entries.append(entry)
                continue
            
            if query_lower in str(extracted_info.get("actions_mentioned", [])).lower():
                matching_entries.append(entry)
                continue
            
            # Search in emotions
            emotional_analysis = entry.get("emotional_analysis", {})
            if query_lower in emotional_analysis.get("primary_emotion", "").lower():
                matching_entries.append(entry)
                continue
            
            # Search in tags
            if query_lower in str(entry.get("tags", [])).lower():
                matching_entries.append(entry)
                continue
        
        return matching_entries
    
    def _format_search_results(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format search results for display"""
        return self._format_recent_entries(entries)
    
    def _analyze_search_patterns(self, matching_entries: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Analyze patterns in search results"""
        if not matching_entries:
            return {"message": f"No patterns found for '{query}'"}
        
        # Analyze decision outcomes for this query
        emotions = []
        quality_scores = []
        
        for entry in matching_entries:
            emotion = entry.get("emotional_analysis", {}).get("primary_emotion")
            if emotion:
                emotions.append(emotion)
            
            score = entry.get("decision_quality", {}).get("percentage")
            if score:
                quality_scores.append(score)
        
        patterns = {
            "total_matches": len(matching_entries),
            "date_range": self._get_date_range(matching_entries),
        }
        
        if emotions:
            patterns["common_emotions"] = self._count_frequency(emotions)
        
        if quality_scores:
            patterns["average_quality"] = round(sum(quality_scores) / len(quality_scores), 1)
            patterns["quality_trend"] = "improving" if len(quality_scores) >= 3 and quality_scores[-1] > quality_scores[0] else "stable"
        
        return patterns