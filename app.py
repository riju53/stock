# app.py

import os
import requests
import streamlit as st
from datetime import datetime
import plotly.graph_objects as go
import pandas as pd
import time

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
# API KEYS (Using hardcoded for now - but better to use secrets)
# =========================================

# Set your Groq API key
GROQ_API_KEY = "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"
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# Finnhub API
FINNHUB_API_KEY = "d87h1n1r01qmhakfpangd87h1n1r01qmhakfpao0"

# AlphaVantage API
ALPHA_VANTAGE_API_KEY = "EXKT5UJD09F47WBW"


# =========================================
# LLM MODEL
# =========================================

@st.cache_resource
def get_model():
    try:
        return ChatGroq(
            model="mixtral-8x7b-32768",  # Changed to a more stable model
            temperature=0.7,
            groq_api_key=GROQ_API_KEY
        )
    except Exception as e:
        st.error(f"Error initializing model: {str(e)}")
        return None

model = get_model()


# =========================================
# TOOLS
# =========================================

@tool
def get_stock_price(symbol: str):
    """Get USA stock price with detailed metrics."""
    
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if "c" not in data or data.get('c') is None:
            return f"❌ Unable to fetch stock price for {symbol.upper()}. Please check the symbol."

        # Calculate change and change percent
        current = data.get('c', 0)
        previous = data.get('pc', current)
        change = current - previous
        change_percent = (change / previous * 100) if previous != 0 else 0
        
        return f"""
📊 **Stock Analysis for {symbol.upper()}** 📊

💰 **Current Price:** ${current:.2f}
📈 **Day's Range:** ${data.get('l', 0):.2f} - ${data.get('h', 0):.2f}
📉 **Open:** ${data.get('o', 0):.2f}
🔙 **Previous Close:** ${previous:.2f}
🔄 **Change:** ${change:.2f} ({change_percent:+.2f}%)
📊 **Volume:** {data.get('v', 0):,}

💡 **Quick Analysis:**
- {'📈 Bullish signal - Price increased' if change > 0 else '📉 Bearish signal - Price decreased'}
- {'🔥 High volatility' if (data.get('h', 0) - data.get('l', 0)) / current > 0.02 else '📊 Normal trading range'}
        """

    except requests.exceptions.RequestException as e:
        return f"❌ Network error fetching stock data: {str(e)}"
    except Exception as e:
        return f"❌ Error fetching stock data: {str(e)}"


@tool
def get_indian_stock_price(symbol: str):
    """Get Indian stock market price with comprehensive details."""
    
    try:
        # Remove .BSE if present for API call
        clean_symbol = symbol.replace('.BSE', '')
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={clean_symbol}.BSE&apikey={ALPHA_VANTAGE_API_KEY}"
        
        response = requests.get(url, timeout=10)
        data = response.json()

        if "Global Quote" not in data or not data["Global Quote"]:
            return f"❌ Unable to fetch Indian stock data for {symbol.upper()}. Please check the symbol."

        quote = data["Global Quote"]
        
        current_price = float(quote.get('05. price', 0))
        previous_close = float(quote.get('08. previous close', 1))
        change = current_price - previous_close
        change_percent = (change / previous_close * 100) if previous_close != 0 else 0

        return f"""
📊 **Stock Analysis for {symbol.upper()}** 📊

💰 **Current Price:** ₹{current_price:,.2f}
📈 **Day's High:** ₹{float(quote.get('03. high', 0)):,.2f}
📉 **Day's Low:** ₹{float(quote.get('04. low', 0)):,.2f}
🔙 **Previous Close:** ₹{previous_close:,.2f}
🔄 **Change:** ₹{change:,.2f} ({change_percent:+.2f}%)
📊 **Volume:** {int(float(quote.get('06. volume', 0))):,}
📈 **Change Percent:** {quote.get('10. change percent', 'N/A')}

💡 **Market Sentiment:**
- {'📈 Positive momentum' if change > 0 else '📉 Negative momentum'}
- {'🔥 High volume activity' if int(float(quote.get('06. volume', 0))) > 1000000 else '📊 Normal trading volume'}
        """

    except requests.exceptions.RequestException as e:
        return f"❌ Network error fetching Indian stock data: {str(e)}"
    except Exception as e:
        return f"❌ Error fetching Indian stock data: {str(e)}"


@tool
def get_company_details(company_name: str):
    """Generate comprehensive company analysis."""
    
    return f"""
🏢 **Company Analysis: {company_name.upper()}** 🏢

### 📋 Company Overview
- **Core Business:** Primary products and services in their industry
- **Market Position:** Competitive advantages and market leadership
- **Global Presence:** International operations and market reach

### 👥 Leadership & Management
- **Executive Team:** Experience and track record
- **Corporate Governance:** Transparency and shareholder relations

### 💼 Financial Health Indicators
- **Revenue Streams:** Diversification and stability
- **Profitability:** Margin analysis and efficiency
- **Growth Metrics:** Historical and projected growth

### 🚀 Growth Opportunities
1. Market expansion possibilities
2. Product innovation pipeline
3. Strategic partnerships
4. Digital transformation initiatives

### ⚠️ Risk Factors to Consider
- Market competition
- Regulatory changes
- Economic cycles
- Operational challenges

### 💎 Investment Insights
- **Short-term (0-12 months):** Key catalysts and events to watch
- **Medium-term (1-3 years):** Growth trajectory and milestones
- **Long-term (3-5+ years):** Industry trends and positioning

### 🎯 Key Metrics to Monitor
- Quarterly earnings reports
- Market share trends
- Customer satisfaction metrics
- R&D investment levels
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
- Risk assessment and investment strategies

**When analyzing stocks, always provide:**
1. Current price and key metrics
2. Price movement analysis
3. Company fundamentals
4. Growth opportunities
5. Risk factors
6. Investment insights

**Response Style:**
- Be professional but enthusiastic
- Use emojis for visual appeal
- Provide actionable insights
- Include both opportunities and risks
- Give clear, balanced recommendations

Always use available tools to fetch real-time data before providing analysis.
"""


# =========================================
# CREATE AGENT
# =========================================

@st.cache_resource
def get_agent():
    if model is None:
        return None
    try:
        return create_react_agent(
            model=model,
            tools=[
                get_stock_price,
                get_indian_stock_price,
                get_company_details
            ],
            prompt=prompt
        )
    except Exception as e:
        st.error(f"Error creating agent: {str(e)}")
        return None

agent = get_agent()


# =========================================
# INITIALIZE SESSION STATE
# =========================================

if 'stock_name' not in st.session_state:
    st.session_state['stock_name'] = "TCS"
if 'market' not in st.session_state:
    st.session_state['market'] = "Indian Stock"


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
            if st.button(f"📈 {stock}", key=f"ind_{stock}", use_container_width=True):
                st.session_state['stock_name'] = stock
                st.session_state['market'] = "Indian Stock"
    
    with st.expander("🇺🇸 USA Stocks", expanded=True):
        usa_stocks = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN"]
        for stock in usa_stocks:
            if st.button(f"📊 {stock}", key=f"usa_{stock}", use_container_width=True):
                st.session_state['stock_name'] = stock
                st.session_state['market'] = "USA Stock"
    
    st.markdown("---")
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 1rem; font-size: 0.8rem;">
        <p>Built with ❤️ by Tathagata Nath</p>
        <p>Data from Finnhub & AlphaVantage</p>
        <p>⚠️ Not financial advice</p>
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
    💡 <strong>Pro Tip:</strong> For Indian stocks, use just the company name (e.g., TCS, INFY). For US stocks, use the symbol (e.g., AAPL, TSLA).
</div>
""", unsafe_allow_html=True)

# Analysis Section
if analyze_button:
    if agent is None:
        st.error("❌ Agent initialization failed. Please check your API keys and try again.")
    else:
        with st.spinner("🤖 AI Agent analyzing stock data..."):
            try:
                # Prepare symbol based on market
                if market == "Indian Stock":
                    symbol = stock_name.upper()
                    user_query = f"""
                    Give complete stock analysis of {symbol} stock from Indian market.
                    Use get_indian_stock_price tool to fetch current price.
                    Use get_company_details tool for company information.
                    Include investment insights and future growth opportunities.
                    """
                else:
                    symbol = stock_name.upper()
                    user_query = f"""
                    Give complete stock analysis of {symbol} stock from USA market.
                    Use get_stock_price tool to fetch current price.
                    Use get_company_details tool for company information.
                    Include investment insights and future growth opportunities.
                    """
                
                # Progress indicators
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("📊 Fetching stock data...")
                progress_bar.progress(25)
                time.sleep(0.5)
                
                # Agent Invocation
                response = agent.invoke({"messages": [("user", user_query)]})
                
                status_text.text("🤔 Analyzing market trends...")
                progress_bar.progress(50)
                time.sleep(0.5)
                
                status_text.text("💡 Generating investment insights...")
                progress_bar.progress(75)
                time.sleep(0.5)
                
                # Final Output
                final_response = response["messages"][-1].content
                
                status_text.text("✅ Analysis complete!")
                progress_bar.progress(100)
                
                # Clear progress indicators
                time.sleep(0.5)
                progress_bar.empty()
                status_text.empty()
                
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
                    
                    Based on the analysis above, consider:
                    - **Risk Assessment:** Align with your risk tolerance
                    - **Entry Strategy:** Look for support levels
                    - **Portfolio Fit:** Ensure proper diversification
                    - **Regular Monitoring:** Track key metrics quarterly
                    """)
                
                with tab3:
                    st.success("""
                    ### 🎯 Recommended Next Steps
                    
                    1. **Due Diligence:** Review company financials and reports
                    2. **Price Alerts:** Set notifications for key levels
                    3. **Position Sizing:** Start with appropriate allocation
                    4. **Exit Strategy:** Define stop-loss and profit targets
                    5. **Review Schedule:** Plan periodic portfolio reviews
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
                st.info("💡 Please check your stock symbol and try again. Make sure you have internet connection.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem;">
    <p>⚠️ <strong>Disclaimer:</strong> This AI tool provides analysis for informational purposes only. 
    Not financial advice. Always consult with a qualified financial advisor before making investment decisions.</p>
    <p style="font-size: 0.8rem;">Built with Streamlit, LangGraph, and Groq | Data sourced from Finnhub & AlphaVantage</p>
</div>
""", unsafe_allow_html=True)
