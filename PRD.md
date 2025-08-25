# Product Requirements Document
# FortunaMind Persistent MCP Server

**Version:** 1.0.0  
**Date:** August 25, 2025  
**Status:** Draft  
**Product Owner:** FortunaMind Team  

---

## Executive Summary

The FortunaMind Persistent MCP Server is a premium add-on service for FortunaMind subscribers that provides advanced technical analysis tools and personal trading journal capabilities through the MCP (Model Context Protocol). Designed specifically for mature professionals (ages 35-65) who are crypto-curious but may have zero cryptocurrency experience, this server extends the basic FortunaMind MCP experience with persistent, personalized features that support a gradual, educational journey into cryptocurrency investing.

---

## 1. Product Vision

### 1.1 Vision Statement
To democratize cryptocurrency investing for mature professionals by providing patient, educational, and persistent tools that transform complete beginners into confident, informed crypto investors at their own pace.

### 1.2 Mission
Guide established professionals through their cryptocurrency journey by providing:
- Technical analysis explained in everyday language
- Personal trading journal for reflection and learning
- Educational insights that adapt to their experience level
- Secure, persistent tracking without complexity

### 1.3 Product Positioning
- **What it is:** An educational companion for crypto-curious professionals
- **What it's not:** A day-trading platform or get-rich-quick tool
- **Key differentiator:** Designed for complete beginners with professional-grade insights

---

## 2. User Analysis

### 2.1 Target User Persona: "The Established Professional Explorer"

**Demographics:**
- **Age:** 35-65
- **Profession:** Established professionals across all industries
- **Income:** $75k-$250k annually
- **Tech Comfort:** Moderate (uses smartphones, online banking)
- **Crypto Experience:** 0-2 years (including complete beginners)
- **Investment Background:** Traditional (401k, stocks, real estate)
- **Initial Crypto Investment:** $1k-$50k

**Psychographics:**
- Risk-aware but curious about new opportunities
- Values education and understanding before acting
- Prefers guided experiences over self-directed learning
- Appreciates patience and clear explanations
- Suspicious of hype, values substance
- Already trusts FortunaMind enough to subscribe

**User Journey:**
1. **Curiosity Phase** - "What is cryptocurrency really?"
2. **Education Phase** - "How do I evaluate crypto investments?"
3. **Experimentation Phase** - "Let me try a small investment"
4. **Learning Phase** - "What worked and what didn't?"
5. **Confidence Phase** - "I understand enough to make informed decisions"

### 2.2 User Needs & Pain Points

**Primary Needs:**
- Start from absolute zero knowledge if needed
- Understand complex concepts in simple terms
- Track decisions to learn from experience
- Build confidence gradually
- Feel secure and protected

**Pain Points:**
- "Crypto seems like it's for young tech people"
- "I don't understand the terminology"
- "I'm afraid of making expensive mistakes"
- "Technical analysis charts look like hieroglyphics"
- "I can't remember why I bought what I bought"

### 2.3 User Stories

**Beginner Stories:**
1. "As someone new to crypto, I want to understand what RSI means in plain English"
2. "As a cautious investor, I want to track my small experimental trades"
3. "As a learner, I want explanations that assume I know nothing"

**Technical Analysis Stories:**
1. "As a subscriber, I want to know if now is a good time to buy BTC, explained simply"
2. "As an investor, I want to understand what 'oversold' actually means for my investment"
3. "As a user, I want indicators translated into buy/hold/sell suggestions"

**Trading Journal Stories:**
1. "As a beginner, I want to record what I was thinking when I made each trade"
2. "As a learner, I want to see which of my strategies actually worked"
3. "As an investor, I want to track my emotional state during trades"

---

## 3. Product Requirements

### 3.1 Core Features

#### 3.1.1 Technical Indicators Tool

**Priority: P0 - Launch Critical**

**Design Principles:**
- Assume zero prior knowledge
- Explain everything in plain English
- Provide educational context
- Offer actionable insights
- Build confidence through understanding

**Supported Indicators with Beginner-Friendly Explanations:**

| Indicator | What It Measures | How It's Explained to Users |
|-----------|-----------------|----------------------------|
| **RSI** | Overbought/Oversold | "Like a pressure gauge - too high means expensive, too low means cheap" |
| **SMA** | Average price trends | "The average price over the last X days - shows general direction" |
| **EMA** | Recent price emphasis | "Like SMA but pays more attention to recent prices" |
| **MACD** | Momentum changes | "Shows when trends might be changing direction" |
| **Volume** | Trading activity | "How many people are buying/selling - high volume means high interest" |
| **Support/Resistance** | Price boundaries | "Prices where Bitcoin tends to stop falling or rising" |

**Example User Interaction:**
```
User: "Should I buy Bitcoin?"

FortunaMind: "Let me check the technical indicators for Bitcoin and explain what they mean:

📊 Bitcoin Analysis (Current Price: $45,234)

🟢 **What the numbers say:**
• RSI: 42 (Slightly cheap - good potential buying range)
• Price vs 50-day average: 2% above (mild bullish trend)
• Volume: High (lots of interest right now)

📚 **What this means in plain English:**
The RSI of 42 is like a sale price - Bitcoin isn't expensive right now. The price being above its 50-day average suggests people have been buying more than selling recently. High volume means this isn't a quiet period - there's real activity.

💡 **For a beginner:**
This could be a reasonable time to make a small purchase if you're thinking about it anyway. Bitcoin isn't screaming "overpriced" right now.

⚠️ **Remember:** No one can predict the future. Only invest what you can afford to lose, and consider starting with a small amount to learn.

Would you like me to explain what any of these indicators mean in more detail?"
```

**Tool Features:**
- **Educational Explanations** - Every indicator comes with plain English explanation
- **Risk Warnings** - Always include appropriate caution for beginners  
- **Context Setting** - Explain market conditions and what they mean
- **Action Guidance** - Gentle suggestions without financial advice
- **Follow-up Education** - Offer deeper explanations if requested

#### 3.1.2 Trading Journal Tool

**Priority: P0 - Launch Critical**

**Design Philosophy:**
- Focus on learning and reflection
- Encourage honest self-assessment
- Track emotions and reasoning, not just numbers
- Build confidence through understanding patterns

**Journal Entry Components:**

**Basic Trade Information:**
- Asset (BTC, ETH, etc.)
- Action (Buy/Sell/Hold Decision)
- Amount (optional - some users prefer privacy)
- Date/Time
- Current Price

**Context & Learning Focus:**
- **Why did you make this decision?** (Free text)
- **What were you feeling?** (Confident, Nervous, FOMO, Researched, Impulsive)
- **What information influenced you?** (News, Technical Analysis, Friend's Advice, etc.)
- **Market conditions** (Automatically captured - trending up/down/sideways)

**Reflection Questions (Optional but Encouraged):**
- What do you hope to learn from this trade?
- If this goes well, what would you do next?
- If this goes poorly, how will you handle it?

**Example Journal Interaction:**
```
User: "Add a journal entry: I bought some Bitcoin because the RSI looked good"

FortunaMind: "I'll help you record this decision. A few quick questions to make this useful for your learning:

📝 **Trade Details:**
✅ Action: Bought Bitcoin
✅ Reason: RSI looked favorable
✅ Date: Today

📚 **Learning Questions** (optional):
• How were you feeling when you made this decision? (confident, nervous, excited, etc.)
• Besides RSI, what else influenced you?
• What are you hoping to learn from this trade?

💡 This is your learning journal - there are no wrong answers, only insights that will help you improve over time.

Would you like to add any of these details, or should I save it as is?"
```

**Journal Analytics (Privacy-First):**
- **Personal Patterns** - "You tend to buy when feeling confident"
- **Learning Insights** - "Your research-based trades performed 20% better" 
- **Emotional Tracking** - "Your best trades happened when you felt calm"
- **Strategy Evolution** - "Your decision-making has become more systematic"
- **Educational Progress** - "You're asking more sophisticated questions"

**Privacy Protection:**
- Dollar amounts are optional
- All data encrypted at rest
- User controls what analytics to show
- Can hide/show specific entries
- Export capability for personal records

### 3.2 User Registration and Security

#### 3.2.1 Registration System

**Subscriber Verification:**
- Integration with FortunaMind subscription system
- Email verification required
- No access without active subscription
- Grace period for payment issues (7 days)

**Registration Flow:**
1. User clicks "Access Persistent Tools" from main FortunaMind interface
2. System checks active subscription status
3. If verified, user creates secure profile
4. Email verification sent
5. Profile activated upon email confirmation
6. Welcome tutorial offered

#### 3.2.2 Security Requirements

**Critical Security Principles:**
- **NEVER store API credentials** - Users provide tokens per session
- **Zero-trust architecture** - Verify every request
- **Data encryption** - AES-256 for all user data at rest
- **Transport security** - TLS 1.3 for all communications
- **Access logging** - Complete audit trail

**Data Protection:**
- All personal data encrypted
- Supabase Row Level Security (RLS) enabled
- User data isolated by subscriber ID
- GDPR compliance ready
- Right to be forgotten implemented

### 3.3 Technical Architecture

#### 3.3.1 Technology Stack

**Core Framework:**
- **Base:** FortunaMind Common Library
- **Server Architecture:** Unified Server
- **Protocol:** MCP (Model Context Protocol)
- **Language:** Python 3.11+

**Storage Layer:**
- **Primary Database:** PostgreSQL on Supabase
- **Real-time Features:** Supabase real-time subscriptions
- **Authentication:** Supabase Auth
- **Security:** Row Level Security (RLS) policies

**API Integration:**
- **Market Data:** Coinbase Advanced Trading API
- **No Stored Credentials:** Users provide API keys per session
- **Rate Limiting:** Respect API limits, intelligent batching
- **Error Handling:** Graceful fallbacks when APIs unavailable

#### 3.3.2 Database Schema

```sql
-- Users table (managed by Supabase Auth)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    subscription_id TEXT NOT NULL, -- Links to FortunaMind subscription
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Technical analysis cache
CREATE TABLE technical_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    analysis_data JSONB NOT NULL,
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    INDEX idx_user_symbol (user_id, symbol),
    INDEX idx_expires (expires_at)
);

-- Trading journal entries
CREATE TABLE journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    action TEXT NOT NULL, -- 'buy', 'sell', 'hold_decision'
    price DECIMAL(20, 8),
    amount DECIMAL(20, 8), -- Optional, encrypted if provided
    reasoning TEXT,
    emotions TEXT[], -- Array of emotion tags
    confidence_level INTEGER CHECK (confidence_level BETWEEN 1 AND 5),
    market_context JSONB, -- Auto-captured market conditions
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_user_date (user_id, created_at DESC),
    INDEX idx_user_symbol (user_id, symbol)
);

-- User preferences
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    preferences JSONB DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security Policies
ALTER TABLE technical_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Users can only access their own data
CREATE POLICY "Users can view own data" ON technical_analysis FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users can insert own data" ON technical_analysis FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can view own entries" ON journal_entries FOR ALL USING (user_id = auth.uid());
CREATE POLICY "Users can view own preferences" ON user_preferences FOR ALL USING (user_id = auth.uid());
```

#### 3.3.3 Tool Integration

**Technical Indicators Tool:**
```python
class PersistentTechnicalIndicatorsTool(ReadOnlyTool):
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="technical_indicators",
            description="Get beginner-friendly technical analysis for cryptocurrencies",
            category=ToolCategory.ANALYTICS,
            permissions=[Permission.READ_ONLY],
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Cryptocurrency symbol (e.g., BTC, ETH)",
                        "enum": ["BTC", "ETH", "LTC", "BCH", "ADA", "SOL"]
                    },
                    "explain_indicators": {
                        "type": "boolean",
                        "description": "Include educational explanations",
                        "default": True
                    },
                    "experience_level": {
                        "type": "string",
                        "description": "User's experience level for appropriate explanations",
                        "enum": ["beginner", "intermediate", "advanced"],
                        "default": "beginner"
                    }
                },
                "required": ["symbol"]
            }
        )

    async def _execute_impl(self, auth_context: AuthContext, **params):
        # 1. Check user registration and subscription status
        # 2. Fetch/calculate technical indicators
        # 3. Format for beginner understanding
        # 4. Cache results in Supabase
        # 5. Return educational analysis
        pass
```

**Trading Journal Tool:**
```python
class TradingJournalTool(WriteEnabledTool):
    @property 
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="trading_journal",
            description="Record and analyze your crypto trading decisions",
            category=ToolCategory.ANALYTICS,
            permissions=[Permission.READ_ONLY, Permission.WRITE],
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add_entry", "view_entries", "get_insights"],
                        "description": "Journal action to perform"
                    },
                    "entry_data": {
                        "type": "object",
                        "description": "Trade entry details (for add_entry)",
                        "properties": {
                            "symbol": {"type": "string"},
                            "trade_action": {"type": "string", "enum": ["buy", "sell", "hold_decision"]},
                            "reasoning": {"type": "string"},
                            "emotions": {"type": "array", "items": {"type": "string"}},
                            "confidence": {"type": "integer", "minimum": 1, "maximum": 5}
                        }
                    }
                },
                "required": ["action"]
            }
        )

    async def _execute_impl(self, auth_context: AuthContext, **params):
        # Handle journal operations with privacy protection
        pass
```

### 3.4 Non-Functional Requirements

#### 3.4.1 Performance
- **Response Time:** < 2 seconds for technical analysis
- **Cache Duration:** 5 minutes for technical data
- **Concurrent Users:** Support 100+ simultaneous users
- **Database Optimization:** Proper indexing for fast queries

#### 3.4.2 Reliability  
- **Uptime:** 99.9% availability
- **Data Backup:** Daily automated backups via Supabase
- **Error Handling:** Graceful degradation when external APIs fail
- **Recovery:** Automatic retry with exponential backoff

#### 3.4.3 Security
- **No Stored Credentials:** API keys never persisted
- **Encryption:** All sensitive data encrypted at rest
- **Authentication:** Supabase Auth integration
- **Authorization:** RLS policies for data isolation
- **Audit Logging:** Complete access logs for security

#### 3.4.4 Usability
- **Learning Curve:** Accessible to complete crypto beginners
- **Error Messages:** Clear, educational error explanations
- **Documentation:** Built-in help and explanations
- **Mobile Friendly:** Works well in mobile MCP clients

---

## 4. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Project setup with FortunaMind Common Library
- [ ] Supabase database setup with RLS policies
- [ ] User registration and authentication system
- [ ] Basic MCP server structure

### Phase 2: Technical Indicators (Weeks 3-4)
- [ ] Technical indicators calculation engine
- [ ] Beginner-friendly explanation system
- [ ] Coinbase API integration (no credential storage)
- [ ] Basic caching layer
- [ ] Initial testing with sample users

### Phase 3: Trading Journal (Weeks 5-6)
- [ ] Journal entry creation and storage
- [ ] Privacy-first data handling
- [ ] Basic analytics and insights
- [ ] User preference management
- [ ] Data export functionality

### Phase 4: Polish & Launch (Weeks 7-8)
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Security audit
- [ ] Documentation completion
- [ ] Beta launch with select subscribers

---

## 5. Success Metrics

### 5.1 User Engagement
- **Primary Metric:** Weekly active users among FortunaMind subscribers
- **Target:** 20% of eligible subscribers using persistent tools monthly
- **Secondary:** Average session duration > 10 minutes
- **Learning Indicator:** Users asking follow-up questions about indicators

### 5.2 Product Success
- **Journal Adoption:** 80% of users create at least 5 journal entries
- **Educational Impact:** Users progress from beginner to intermediate explanations
- **Retention:** 70% of users return within 30 days
- **User Satisfaction:** NPS > 60

### 5.3 Technical Performance
- **Response Time:** 95% of requests < 2 seconds
- **Uptime:** > 99.9% availability
- **Security:** Zero security incidents
- **Data Integrity:** Zero data loss incidents

### 5.4 Business Impact
- **Subscription Retention:** Improved retention for users of persistent tools
- **Upgrade Rate:** Track conversion from basic to persistent tools
- **Support Reduction:** Fewer basic crypto education support requests
- **Word of Mouth:** Organic user referrals and positive reviews

---

## 6. Risk Management

### 6.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Supabase service outage | Low | High | Local backup systems, status monitoring |
| Coinbase API rate limits | Medium | Medium | Intelligent caching, multiple data sources |
| Performance issues with growth | Medium | High | Performance monitoring, optimization plan |
| Security vulnerabilities | Low | Critical | Security audit, penetration testing |

### 6.2 Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Low adoption rate | Medium | High | Beta testing, user feedback integration |
| Subscription cancellations | Low | Medium | Gradual rollout, value demonstration |
| Regulatory compliance issues | Low | High | Legal review, conservative approach |
| User data privacy concerns | Low | Critical | Transparent privacy policy, minimal data collection |

### 6.3 User Experience Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Too complex for beginners | Medium | High | Extensive user testing, iterative design |
| Not valuable enough | Medium | High | Focus on learning outcomes, user interviews |
| Technical indicators confusing | High | Medium | Plain English explanations, progressive disclosure |

---

## 7. Compliance & Legal

### 7.1 Financial Regulations
- **Not Financial Advice:** Clear disclaimers on all outputs
- **Educational Purpose:** Position as educational tool only
- **Risk Warnings:** Appropriate warnings on all analysis
- **No Guaranteed Returns:** Clear communication about investment risks

### 7.2 Data Protection
- **GDPR Compliance:** Right to access, rectify, and delete data
- **Data Minimization:** Collect only necessary information
- **Consent Management:** Clear opt-in for data collection
- **Data Retention:** Automatic deletion of expired cache data

### 7.3 Terms of Service
- Subscription required for access
- Educational use only
- No financial advice provided
- User responsible for investment decisions
- Data usage and privacy terms

---

## 8. Appendices

### Appendix A: Technical Indicator Definitions

**For Internal Development Reference:**

| Indicator | Formula | Parameters | Cache Duration |
|-----------|---------|------------|----------------|
| RSI | RSI = 100 - (100 / (1 + RS)) | Period: 14 days | 5 minutes |
| SMA | (P1 + P2 + ... + Pn) / n | Periods: 20, 50, 200 days | 5 minutes |
| EMA | EMA = (P * (2/(n+1))) + (EMA_prev * (1-(2/(n+1)))) | Periods: 12, 26 days | 5 minutes |
| MACD | MACD = EMA12 - EMA26 | Signal: 9-day EMA | 5 minutes |
| Volume | Sum of trading volume | Period: 24 hours | 5 minutes |

### Appendix B: Beginner Education Framework

**Explanation Levels:**
1. **Complete Beginner:** Assume no crypto knowledge
2. **Basic Understanding:** Knows crypto basics, learning analysis
3. **Intermediate:** Comfortable with basic indicators

**Explanation Structure:**
1. What it measures (simple analogy)
2. Why it matters (practical impact)  
3. How to interpret (actionable guidance)
4. What to watch for (risk awareness)
5. Further learning (optional deep dive)

### Appendix C: Privacy by Design

**Data Collection Principles:**
- Collect minimum necessary data
- User controls over data visibility
- Automatic expiration of cache data
- Encryption of all sensitive information
- No sharing with third parties
- Complete deletion on account closure

---

**Document Approval**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| Technical Lead | | | |
| Security Officer | | | |
| Legal Counsel | | | |

---

*This PRD serves as the foundation for developing the FortunaMind Persistent MCP Server with a focus on education, security, and user empowerment.*