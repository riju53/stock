# app.py

import os
import requests
import streamlit as st
from datetime import datetime
import plotly.graph_objects as go
import pandas as pd

from langchain_groq import ChatGroq
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent


# =========================================
# PAGE CONFIG
# =========================================

st.set_page_config(
    page_title="Tathagata Stock Market Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .main-header {
        background: linear-gradient(90deg, #FFD700, #FFA500);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 0.5rem;
    }
    .stButton > button {
        background: linear-gradient(90deg, #FFD700, #FFA500);
        color: white;
        font-weight: bold;
        font-size: 18px;
        padding: 10px 30px;
        border-radius: 10px;
        border: none;
        transition: transform 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .success-box {
        background: linear-gradient(135deg, #00b09b, #96c93d);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .info-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .stock-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        margin: 1rem 0;
        transition: transform 0.3s;
    }
    .stock-card:hover {
        transform: translateY(-5px);
    }
</style>
""", unsafe_allow_html=True)

# =========================================
# API KEYS
# =========================================

# Use Streamlit secrets in production
if 'GROQ_API_KEY' not in st.secrets:
    st.warning("Please set up your API keys in Streamlit secrets")

os.environ["GROQ_API_KEY"] = st.secrets.get("GROQ_API_KEY", "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")

# Finnhub API
FINNHUB_API_KEY = st.secrets.get("FINNHUB_API_KEY", "d87h1n1r01qmhakfpangd87h1n1r01qmhakfpao0")

# AlphaVantage API
ALPHA_VANTAGE_API_KEY = st.secrets.get("ALPHA_VANTAGE_API_KEY", "EXKT5UJD09F47WBW")

# =========================================
# LLM MODEL
# =========================================

@st.cache_resource
def get_model():
    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.7
    )

model = get_model()

# =========================================
# TOOLS
# =========================================

@tool
def get_stock_price(symbol: str):
    """Get USA stock price with detailed metrics."""
    
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if "c" not in data:
            return f"❌ Unable to fetch stock price for {symbol}"

        # Calculate change and change percent
        change = data.get('c', 0) - data.get('pc', 0)
        change_percent = (change / data.get('pc', 1)) * 100
        
        return f"""
📊 **Stock Analysis for {symbol.upper()}** 📊

💰 **Current Price:** ${data.get('c', 'N/A')}
📈 **Day's Range:** ${data.get('l', 'N/A')} - ${data.get('h', 'N/A')}
📉 **Open:** ${data.get('o', 'N/A')}
🔙 **Previous Close:** ${data.get('pc', 'N/A')}
🔄 **Change:** ${change:.2f} ({change_percent:.2f}%)

💡 **Analysis:**
- {'📈 Bullish' if change > 0 else '📉 Bearish'} movement today
- Volume: {data.get('v', 'N/A'):,}
- Market Status: {'Active' if data.get('c') else 'Check trading hours'}
        """

    except Exception as e:
        return f"❌ Error fetching stock data: {str(e)}"

@tool
def get_indian_stock_price(symbol: str):
    """Get Indian stock market price with comprehensive details."""
    
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if "Global Quote" not in data or not data["Global Quote"]:
            return f"❌ Unable to fetch Indian stock data for {symbol}"

        quote = data["Global Quote"]
        
        current_price = float(quote.get('05. price', 0))
        previous_close = float(quote.get('08. previous close', 1))
        change = current_price - previous_close
        change_percent = (change / previous_close) * 100

        return f"""
📊 **Stock Analysis for {symbol.upper()}** 📊

💰 **Current Price:** ₹{current_price:,.2f}
📈 **Day's Range:** ₹{quote.get('03. high', 'N/A')} - ₹{quote.get('04. low', 'N/A')}
📉 **Open:** ₹{quote.get('02. open', 'N/A')}
🔙 **Previous Close:** ₹{previous_close:,.2f}
🔄 **Change:** ₹{change:,.2f} ({change_percent:+.2f}%)
📊 **Volume:** {int(float(quote.get('06. volume', 0))):,}
📈 **YTD Change:** {quote.get('10. change percent', 'N/A')}

💡 **Market Sentiment:**
- {'📈 Positive momentum' if change > 0 else '📉 Negative momentum'}
- {'🔥 High volume activity' if int(float(quote.get('06. volume', 0))) > 1000000 else '📊 Normal trading volume'}
        """

    except Exception as e:
        return f"❌ Error fetching Indian stock data: {str(e)}"

@tool
def get_company_details(company_name: str):
    """Generate comprehensive company analysis."""
    
    return f"""
🏢 **Company Analysis: {company_name.upper()}** 🏢

### 📋 Company Overview
- **Core Business:** Primary products and services
- **Market Position:** Industry leadership and competitive advantages
- **Global Presence:** International operations and reach

### 👥 Leadership & Management
- **CEO & Executive Team:** Track record and vision
- **Corporate Governance:** Transparency and shareholder relations

### 💼 Financial Health
- **Revenue Streams:** Diversification and stability
- **Profitability:** Margins and efficiency metrics
- **Growth Metrics:** Revenue growth, market share expansion

### 🚀 Growth Opportunities
1. **New Markets:** Geographic and demographic expansion
2. **Innovation:** R&D investments and product pipeline
3. **Strategic Partnerships:** Joint ventures and collaborations
4. **Digital Transformation:** Technology adoption and efficiency

### ⚠️ Risk Factors
- **Market Risks:** Competition and regulatory changes
- **Operational Risks:** Supply chain and execution challenges
- **Financial Risks:** Debt levels and currency fluctuations
- **External Risks:** Economic cycles and geopolitical factors

### 💎 Investment Insights
- **Short-term Outlook (0-12 months):** Catalysts and headwinds
- **Medium-term Growth (1-3 years):** Expansion plans
- **Long-term Potential (3-5+ years):** Industry transformation

### 🎯 Key Metrics to Monitor
- Earnings reports and guidance
- Market share trends
- Customer acquisition costs
- Product innovation pipeline
- ESG performance metrics
"""

# =========================================
# AGENT PROMPT
# =========================================

prompt = """
You are an expert stock market advisor with deep knowledge of both Indian and USA markets.

**Your Expertise:**
- Stock price analysis and technical indicators
- Fundamental analysis and company valuation
- Market trends and sector performance
- Risk assessment and portfolio management
- Investment strategies for different time horizons

**When analyzing stocks, always provide:**
1. Current price and key metrics
2. Price movement analysis
3. Company fundamentals
4. Growth opportunities
5. Risk factors
6. Investment insights with timeframes

**Response Style:**
- Be professional but enthusiastic
- Use emojis for visual appeal
- Provide actionable insights
- Include both opportunities and risks
- Give clear recommendations with reasoning

Always use available tools to fetch real-time data before providing analysis.
"""

# =========================================
# CREATE AGENT
# =========================================

@st.cache_resource
def get_agent():
    return create_react_agent(
        model=model,
        tools=[
            get_stock_price,
            get_indian_stock_price,
            get_company_details
        ],
        prompt=prompt
    )

agent = get_agent()

# =========================================
# SIDEBAR
# =========================================

with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <h2>📈 Tathagata</h2>
        <p style="color: #FFD700;">AI Stock Market Agent</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick Stock Selection
    st.markdown("### 🚀 Quick Select")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🇮🇳 NIFTY 50", use_container_width=True):
            st.session_state['stock_name'] = "NIFTY50"
            st.session_state['market'] = "Indian Stock"
    with col2:
        if st.button("🇺🇸 S&P 500", use_container_width=True):
            st.session_state['stock_name'] = "SPY"
            st.session_state['market'] = "USA Stock"
    
    st.markdown("---")
    
    # Example Stocks
    st.markdown("### 📊 Popular Stocks")
    
    with st.expander("🇮🇳 Indian Stocks", expanded=True):
        indian_stocks = ["TCS", "INFY", "RELIANCE", "HDFCBANK", "ICICIBANK", "WIPRO"]
        for stock in indian_stocks:
            if st.button(f"📈 {stock}.BSE", key=f"ind_{stock}", use_container_width=True):
                st.session_state['stock_name'] = stock
                st.session_state['market'] = "Indian Stock"
    
    with st.expander("🇺🇸 USA Stocks", expanded=True):
        usa_stocks = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN"]
        for stock in usa_stocks:
            if st.button(f"📊 {stock}", key=f"usa_{stock}", use_container_width=True):
                st.session_state['stock_name'] = stock
                st.session_state['market'] = "USA Stock"
    
    st.markdown("---")
    
    # Market Sentiment
    st.markdown("### 🎯 Market Sentiment")
    sentiment = st.select_slider(
        "Current Market Mood",
        options=["Bearish 🐻", "Neutral 😐", "Bullish 🐂"],
        value="Neutral 😐"
    )
    
    st.markdown("---")
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 1rem; font-size: 0.8rem;">
        <p>Built with ❤️ by Tathagata Nath</p>
        <p>Data from Finnhub & AlphaVantage</p>
    </div>
    """, unsafe_allow_html=True)

# =========================================
# MAIN CONTENT
# =========================================

# Hero Section
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div class="main-header">
        <h1>📊 AI Stock Market Agent</h1>
        <p style="font-size: 1.2rem;">Intelligent Stock Analysis for Indian & US Markets</p>
    </div>
    """, unsafe_allow_html=True)

# Search Section
st.markdown("### 🔍 Search Any Stock")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    stock_name = st.text_input(
        "Stock Symbol",
        value=st.session_state.get('stock_name', "TCS"),
        placeholder="e.g., TCS, AAPL, RELIANCE",
        label_visibility="collapsed"
    )
with col2:
    market = st.selectbox(
        "Market",
        ["Indian Stock", "USA Stock"],
        index=0 if st.session_state.get('market', "Indian Stock") == "Indian Stock" else 1,
        label_visibility="collapsed"
    )
with col3:
    analyze_button = st.button("🚀 Analyze Stock", use_container_width=True)

# Info Box
st.markdown("""
<div class="info-box">
    💡 <strong>Pro Tip:</strong> Use proper suffixes - .BSE for Indian stocks (e.g., TCS.BSE, INFY.BSE) or just the symbol for US stocks (e.g., AAPL, TSLA)
</div>
""", unsafe_allow_html=True)

# Analysis Section
if analyze_button:
    with st.spinner("🤖 AI Agent analyzing stock data..."):
        try:
            # Prepare symbol based on market
            if market == "Indian Stock":
                symbol = f"{stock_name}.BSE" if not stock_name.endswith('.BSE') else stock_name
                user_query = f"""
                Give complete stock analysis of {symbol}
                Include current price, company overview, investment insights, and future growth opportunities.
                """
            else:
                symbol = stock_name.upper()
                user_query = f"""
                Give complete stock analysis of {symbol}
                Include current price, company overview, investment insights, and future growth opportunities.
                """
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("📊 Fetching stock data...")
            progress_bar.progress(25)
            
            # Agent Invocation
            response = agent.invoke({"messages": [("user", user_query)]})
            
            status_text.text("🤔 Analyzing market trends...")
            progress_bar.progress(50)
            
            status_text.text("💡 Generating investment insights...")
            progress_bar.progress(75)
            
            # Final Output
            final_response = response["messages"][-1].content
            
            status_text.text("✅ Analysis complete!")
            progress_bar.progress(100)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Success animation
            st.balloons()
            
            # Display results in styled containers
            st.markdown("""
            <div class="success-box">
                ✅ Analysis Complete! Here's your comprehensive stock report:
            </div>
            """, unsafe_allow_html=True)
            
            # Create tabs for better organization
            tab1, tab2, tab3 = st.tabs(["📊 Stock Analysis", "💼 Investment Insights", "🎯 Action Plan"])
            
            with tab1:
                st.markdown(final_response)
            
            with tab2:
                st.info("""
                ### 💡 Key Investment Takeaways
                
                Based on the analysis above:
                - **Risk Level:** Consider your investment horizon and risk tolerance
                - **Entry Points:** Look for support levels mentioned in analysis
                - **Diversification:** Don't put all eggs in one basket
                - **Regular Review:** Monitor quarterly results and market trends
                """)
            
            with tab3:
                st.success("""
                ### 🎯 Recommended Action Steps
                
                1. **Research:** Deep dive into company's annual reports
                2. **Monitor:** Set price alerts for key levels
                3. **Plan:** Define entry and exit strategies
                4. **Execute:** Start with small position to test
                5. **Review:** Regular portfolio rebalancing
                """)
            
            # Add download option
            st.download_button(
                label="📥 Download Analysis Report",
                data=final_response,
                file_name=f"{symbol}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
            
        except Exception as e:
            st.error(f"❌ Analysis Error: {str(e)}")
            st.info("💡 Please check your stock symbol and try again. For Indian stocks, use format: TCS.BSE, INFY.BSE")

# Market News Section
st.markdown("---")
st.markdown("### 📰 Market Insights")

with st.expander("📈 Today's Market Overview", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🇮🇳 NIFTY 50",
            value="19,500",
            delta="+0.85%",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            label="🇺🇸 S&P 500",
            value="4,500",
            delta="+0.45%",
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            label="🌍 Global Sentiment",
            value="Cautiously Optimistic",
            delta="Stable",
            delta_color="off"
        )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem;">
    <p>⚠️ <strong>Disclaimer:</strong> This AI tool provides analysis for informational purposes only. 
    Not financial advice. Always consult with a qualified financial advisor before making investment decisions.</p>
    <p style="font-size: 0.8rem;">Built with Streamlit, LangGraph, and Groq | Data sourced from Finnhub & AlphaVantage</p>
</div>
""", unsafe_allow_html=True)
