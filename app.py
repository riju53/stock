# app.py

import os
import requests
import streamlit as st

from langchain_groq import ChatGroq
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent


# ==============================
# STREAMLIT PAGE CONFIG
# ==============================

st.set_page_config(
    page_title="AI Stock Market Agent",
    page_icon="📈",
    layout="wide"
)

st.title("📈 AI Stock Market Agent")
st.markdown("Get live stock prices and company insights using AI agents.")


# ==============================
# API KEYS
# ==============================

# Set your Groq API key here
os.environ["GROQ_API_KEY"] = "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"

# Finnhub API
API_KEY = "d87h1n1r01qmhakfpangd87h1n1r01qmhakfpao0"

# AlphaVantage API
API_KEY1 = "EXKT5UJD09F47WBW"


# ==============================
# LLM MODEL
# ==============================

model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=1.5
)


# ==============================
# TOOLS
# ==============================

@tool
def get_stock_price(symbol: str):
    """
    Get live USA stock price using Finnhub API.
    Example: AAPL, TSLA, NVDA
    """

    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"

    response = requests.get(url)
    data = response.json()

    return f"""
    Stock: {symbol}

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
    RELIANCE.BSE
    TCS.BSE
    INFY.BSE
    """

    url = (
        f"https://www.alphavantage.co/query?"
        f"function=GLOBAL_QUOTE"
        f"&symbol={symbol}"
        f"&apikey={API_KEY1}"
    )

    response = requests.get(url)
    data = response.json()

    try:
        quote = data["Global Quote"]

        return f"""
        Stock: {symbol}

        Current Price: ₹{quote['05. price']}
        Open Price: ₹{quote['02. open']}
        High Price: ₹{quote['03. high']}
        Low Price: ₹{quote['04. low']}
        Previous Close: ₹{quote['08. previous close']}
        Volume: {quote['06. volume']}
        Change Percent: {quote['10. change percent']}
        """

    except Exception as e:
        return f"Error fetching stock data: {e}"


@tool
def get_indian_stock_details(symbol: str):
    """
    Get Indian company details.
    Example:
    TCS.BSE
    INFY.BSE
    """

    return f"""
    Generate detailed company information about {symbol}.

    Include:
    - Company overview
    - Business model
    - CEO
    - Industry
    - Revenue sources
    - Growth opportunities
    - Risks
    """


@tool
def get_usa_stock_details(symbol: str):
    """
    Get USA company details.

    Example:
    AAPL
    TSLA
    NVDA
    """

    return f"""
    Generate detailed company information about {symbol}.

    Include:
    - Company overview
    - Business model
    - CEO
    - Industry
    - Revenue sources
    - Growth opportunities
    - Risks
    """


# ==============================
# USER INPUT
# ==============================

col1, col2 = st.columns(2)

with col1:
    stock_name = st.text_input(
        "Enter Stock Name",
        value="TCS"
    )

with col2:
    market = st.selectbox(
        "Select Market",
        ["Indian Stock", "USA Stock"]
    )


# ==============================
# CREATE AGENT
# ==============================

prompt = f"""
You are an expert stock market advisor.

Provide:
1. Stock name
2. Current stock price
3. High price
4. Low price
5. Open price
6. Previous close
7. Company overview
8. Investment insights
9. Risks
10. Future growth opportunities

Keep the explanation under 1000 words.
"""


agent = create_react_agent(
    model=model,
    tools=[
        get_stock_price,
        get_indian_stock_price,
        get_indian_stock_details,
        get_usa_stock_details
    ],
    prompt=prompt
)


# ==============================
# BUTTON ACTION
# ==============================

if st.button("🚀 Analyze Stock"):

    with st.spinner("Analyzing stock..."):

        try:

            if market == "Indian Stock":
                user_query = f"""
                What is the current stock price and company analysis of {stock_name}.BSE
                """

            else:
                user_query = f"""
                What is the current stock price and company analysis of {stock_name}
                """

            response = agent.invoke(
                {
                    "input": user_query
                }
            )

            final_response = response["messages"][-1].content

            st.success("Analysis Complete ✅")

            st.markdown("## 📊 Stock Analysis")
            st.write(final_response)

        except Exception as e:
            st.error(f"Error: {e}")


# ==============================
# SIDEBAR
# ==============================

st.sidebar.title("📌 Example Stocks")

st.sidebar.markdown("""
### 🇮🇳 Indian Stocks
- TCS.BSE
- INFY.BSE
- RELIANCE.BSE
- HDFCBANK.BSE

### 🇺🇸 USA Stocks
- AAPL
- TSLA
- NVDA
- MSFT
""")


# ==============================
# FOOTER
# ==============================

st.markdown("---")
st.caption("Built using Streamlit + LangGraph + Groq")
