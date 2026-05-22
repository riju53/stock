# app.py

import os
import requests
import streamlit as st

from langchain_groq import ChatGroq
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent


# =========================================
# PAGE CONFIG
# =========================================

st.set_page_config(
    page_title="AI Stock Market Agent",
    page_icon="📈",
    layout="wide"
)

st.title("📈 AI Stock Market Agent")
st.markdown("Analyze Indian and USA stocks using AI agents.")


# =========================================
# API KEYS
# =========================================

# Set your Groq API key here
os.environ["GROQ_API_KEY"] = "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"

# Finnhub API
API_KEY = "d87h1n1r01qmhakfpangd87h1n1r01qmhakfpao0"

# AlphaVantage API
API_KEY1 = "G1KWHKEHXDZ1HU6A"


# =========================================
# LLM MODEL
# =========================================

model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=1
)


# =========================================
# TOOLS
# =========================================

@tool
def get_stock_price(symbol: str):
    """
    Get USA stock price.

    Example:
    AAPL
    TSLA
    NVDA
    """

    url = (
        f"https://finnhub.io/api/v1/quote?"
        f"symbol={symbol}"
        f"&token={FINNHUB_API_KEY}"
    )

    response = requests.get(url)
    data = response.json()

    if "c" not in data:
        return f"Unable to fetch stock price for {symbol}"

    return f"""
    USA Stock: {symbol}

    Current Price: ${data.get('c')}
    High Price: ${data.get('h')}
    Low Price: ${data.get('l')}
    Open Price: ${data.get('o')}
    Previous Close: ${data.get('pc')}
    """


@tool
def get_indian_stock_price(symbol: str):
    """
    Get Indian stock market price.

    Example:
    TCS.BSE
    INFY.BSE
    RELIANCE.BSE
    """

    url = (
        f"https://www.alphavantage.co/query?"
        f"function=GLOBAL_QUOTE"
        f"&symbol={symbol}"
        f"&apikey={ALPHA_VANTAGE_API_KEY}"
    )

    response = requests.get(url)
    data = response.json()

    try:
        quote = data["Global Quote"]

        return f"""
        Indian Stock: {symbol}

        Current Price: ₹{quote['05. price']}
        Open Price: ₹{quote['02. open']}
        High Price: ₹{quote['03. high']}
        Low Price: ₹{quote['04. low']}
        Previous Close: ₹{quote['08. previous close']}
        Volume: {quote['06. volume']}
        Change Percent: {quote['10. change percent']}
        """

    except Exception:
        return f"Unable to fetch Indian stock data for {symbol}"


@tool
def get_company_details(company_name: str):
    """
    Generate detailed company analysis.

    Example:
    TCS
    AAPL
    TSLA
    """

    return f"""
    Generate detailed analysis for company {company_name}

    Include:
    - Company overview
    - CEO
    - Industry
    - Products and services
    - Revenue sources
    - Market position
    - Future growth opportunities
    - Risks
    - Investment insights
    """


# =========================================
# AGENT PROMPT
# =========================================

prompt = """
You are an expert stock market advisor.

Your tasks:
- Fetch stock prices
- Explain company details
- Analyze stock performance
- Give investment insights
- Explain future opportunities and risks

Always use tools whenever stock information is requested.
"""


# =========================================
# CREATE AGENT
# =========================================

agent = create_react_agent(
    model=model,
    tools=[
        get_stock_price,
        get_indian_stock_price,
        get_company_details
    ],
    prompt=prompt
)


# =========================================
# USER INPUT
# =========================================

col1, col2 = st.columns(2)

with col1:
    stock_name = st.text_input(
        "Enter Stock Symbol",
        value="TCS"
    )

with col2:
    market = st.selectbox(
        "Select Market",
        [
            "Indian Stock",
            "USA Stock"
        ]
    )


# =========================================
# ANALYZE BUTTON
# =========================================

if st.button("🚀 Analyze Stock"):

    with st.spinner("Analyzing stock..."):

        try:

            # Indian Stocks
            if market == "Indian Stock":

                symbol = f"{stock_name}.BSE"

                user_query = f"""
                Give complete stock analysis of {symbol}

                Include:
                - current price
                - open price
                - high price
                - low price
                - previous close
                - volume
                - company overview
                - investment insights
                - future growth opportunities
                """

            # USA Stocks
            else:

                symbol = stock_name

                user_query = f"""
                Give complete stock analysis of {symbol}

                Include:
                - current price
                - open price
                - high price
                - low price
                - previous close
                - company overview
                - investment insights
                - future growth opportunities
                """

            # Agent Invocation
            response = agent.invoke(
                {
                    "messages": [
                        ("user", user_query)
                    ]
                }
            )

            # Final Output
            final_response = response["messages"][-1].content

            st.success("Analysis Complete ✅")

            st.markdown("## 📊 Stock Analysis")

            st.write(final_response)

        except Exception as e:

            st.error(f"Error: {str(e)}")


# =========================================
# SIDEBAR
# =========================================

st.sidebar.title("📌 Example Stocks")

st.sidebar.markdown("""
### 🇮🇳 Indian Stocks
- TCS
- INFY
- RELIANCE
- HDFCBANK

### 🇺🇸 USA Stocks
- AAPL
- TSLA
- NVDA
- MSFT
""")


# =========================================
# FOOTER
# =========================================

st.markdown("---")
st.caption("Built with Streamlit + LangGraph + Groq")
