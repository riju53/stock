# =========================================
# IMPORTS
# =========================================

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
    page_title="Tathagata Financial AI Agent",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Tathagata Financial Market Advisor")
st.markdown(
    "Analyze Indian stocks, USA stocks, and Mutual funds using AI."
)


# =========================================
# API KEYS
# =========================================

# Set Groq API Key
#os.environ["GROQ_API_KEY"] = "YOUR_GROQ_API_KEY"

# Finnhub API Key
#FINNHUB_API_KEY = "YOUR_FINNHUB_API_KEY"

# Alpha Vantage API Key
#ALPHA_VANTAGE_API_KEY = "YOUR_ALPHA_VANTAGE_API_KEY"

# Set your Groq API key here
#os.environ["GROQ_API_KEY"] = "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"
os.environ["GROQ_API_KEY"] = "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"

# Finnhub API
FINNHUB_API_KEY = "d87h1n1r01qmhakfpangd87h1n1r01qmhakfpao0"
API_KEY = FINNHUB_API_KEY

# AlphaVantage API
ALPHA_VANTAGE_API_KEY = "EXKT5UJD09F47WBW"
API_KEY1 = ALPHA_VANTAGE_API_KEY


# =========================================
# LLM MODEL
# =========================================

model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.7
)


# =========================================
# USA STOCK TOOL
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

    try:

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
        USA Stock Analysis

        Stock Symbol: {symbol}

        Current Price: ${data.get('c')}

        High Price: ${data.get('h')}

        Low Price: ${data.get('l')}

        Open Price: ${data.get('o')}

        Previous Close: ${data.get('pc')}
        """

    except Exception as e:

        return f"Error fetching USA stock data: {str(e)}"


# =========================================
# INDIAN STOCK TOOL
# =========================================

@tool
def get_indian_stock_price(symbol: str):
    """
    Get Indian stock market data.

    Example:
    TCS.BSE
    INFY.BSE
    RELIANCE.BSE
    """

    try:

        url = (
            f"https://www.alphavantage.co/query?"
            f"function=GLOBAL_QUOTE"
            f"&symbol={symbol}"
            f"&apikey={ALPHA_VANTAGE_API_KEY}"
        )

        response = requests.get(url)

        data = response.json()

        quote = data["Global Quote"]

        return f"""
        Indian Stock Analysis

        Stock Symbol: {symbol}

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


# =========================================
# COMPANY DETAILS TOOL
# =========================================

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
    Generate detailed company analysis for {company_name}

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
# SEARCH MUTUAL FUND
# =========================================

def search_fund(name):

    url = f"https://api.mfapi.in/mf/search?q={name}"

    response = requests.get(url)

    data = response.json()

    if not data:
        return None

    return data[0]


# =========================================
# MUTUAL FUND ANALYZER TOOL
# =========================================

@tool
def analyze_mutual_fund(fund_name: str):
    """
    Analyze Indian mutual fund using fund name.

    Example:
    SBI Small Cap Fund
    """

    try:

        # Search scheme
        fund = search_fund(fund_name)

        if not fund:
            return "Mutual fund not found."

        scheme_code = fund["schemeCode"]

        scheme_name = fund["schemeName"]

        # Fetch NAV history
        url = f"https://api.mfapi.in/mf/{scheme_code}"

        response = requests.get(url)

        data = response.json()

        nav_data = data["data"]

        if not nav_data:
            return "No NAV data available."

        latest = nav_data[0]

        oldest = nav_data[-1]

        latest_nav = float(latest["nav"])

        oldest_nav = float(oldest["nav"])

        growth = (
            (latest_nav - oldest_nav)
            / oldest_nav
        ) * 100

        # 30 Day NAV Average
        recent_navs = [
            float(item["nav"])
            for item in nav_data[:30]
        ]

        avg_nav = sum(recent_navs) / len(recent_navs)

        # Risk Logic
        if growth > 300:
            risk = "High Growth / Moderate Risk"

        elif growth > 100:
            risk = "Moderate Growth"

        else:
            risk = "Low Growth"

        return f"""
        Mutual Fund Analysis

        Fund Name: {scheme_name}

        Scheme Code: {scheme_code}

        Latest NAV: ₹{latest_nav}

        Old NAV: ₹{oldest_nav}

        Overall Growth: {growth:.2f}%

        30-Day Average NAV: ₹{avg_nav:.2f}

        Risk Level: {risk}

        Latest NAV Date: {latest['date']}

        Historical Records: {len(nav_data)}

        Investment Insight:
        This mutual fund has shown
        {growth:.2f}% growth historically.
        """

    except Exception as e:

        return f"Error analyzing mutual fund: {str(e)}"


# =========================================
# AGENT PROMPT
# =========================================

prompt = """
You are an expert financial advisor.

Your tasks:
- Analyze Indian stocks
- Analyze USA stocks
- Analyze Indian mutual funds
- Explain company details
- Give investment insights
- Explain opportunities and risks

Always use tools whenever financial
information is requested.

For mutual funds use:
analyze_mutual_fund tool.

For USA stocks use:
get_stock_price tool.

For Indian stocks use:
get_indian_stock_price tool.
"""


# =========================================
# CREATE AGENT
# =========================================

agent = create_react_agent(
    model=model,
    tools=[
        get_stock_price,
        get_indian_stock_price,
        get_company_details,
        analyze_mutual_fund
    ],
    prompt=prompt
)


# =========================================
# USER INPUT
# =========================================

col1, col2 = st.columns(2)

with col1:

    stock_name = st.text_input(
        "Enter Stock / Mutual Fund Name",
        value="TCS"
    )

with col2:

    market = st.selectbox(
        "Select Market",
        [
            "Indian Stock",
            "USA Stock",
            "Mutual Fund"
        ]
    )


# =========================================
# ANALYZE BUTTON
# =========================================

if st.button("🚀 Analyze"):

    with st.spinner("Analyzing financial data..."):

        try:

            # =========================================
            # INDIAN STOCK
            # =========================================

            if market == "Indian Stock":

                symbol = f"{stock_name}.BSE"

                user_query = f"""
                Give complete analysis of {symbol}

                Include:
                - current price
                - open price
                - high price
                - low price
                - previous close
                - volume
                - company overview
                - investment insights
                - future opportunities
                """

            # =========================================
            # USA STOCK
            # =========================================

            elif market == "USA Stock":

                symbol = stock_name

                user_query = f"""
                Give complete analysis of {symbol}

                Include:
                - current price
                - open price
                - high price
                - low price
                - previous close
                - company overview
                - investment insights
                - future opportunities
                """

            # =========================================
            # MUTUAL FUND
            # =========================================

            else:

                user_query = f"""
                Analyze mutual fund {stock_name}

                Include:
                - latest NAV
                - overall growth
                - risk level
                - investment insight
                - long term outlook
                """

            # =========================================
            # AGENT INVOCATION
            # =========================================

            response = agent.invoke(
                {
                    "messages": [
                        ("user", user_query)
                    ]
                }
            )

            final_response = (
                response["messages"][-1].content
            )

            # =========================================
            # OUTPUT
            # =========================================

            st.success("Analysis Complete ✅")

            st.markdown("## 📊 Financial Analysis")

            st.write(final_response)

        except Exception as e:

            st.error(f"Error: {str(e)}")


# =========================================
# SIDEBAR
# =========================================

st.sidebar.title("📌 Example Inputs")

st.sidebar.markdown("""
## 🇮🇳 Indian Stocks
- TCS
- INFY
- RELIANCE
- HDFCBANK

## 🇺🇸 USA Stocks
- AAPL
- TSLA
- NVDA
- MSFT

## 💰 Mutual Funds
- SBI Small Cap Fund
- Parag Parikh Flexi Cap Fund
- HDFC Flexi Cap Fund
- ICICI Prudential Bluechip Fund
""")


# =========================================
# FOOTER
# =========================================

st.markdown("---")

st.caption(
    "Built with Streamlit + LangChain + Groq "
    "by Tathagata Nath"
)
