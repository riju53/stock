import streamlit as st
from langchain_groq import ChatGroq
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
import requests

# Page configuration
st.set_page_config(
    page_title="Stock Market Advisor Agent",
    page_icon="📈",
    layout="wide"
)

# Title and description
st.title("📈 Stock Market Advisor Agent")
st.markdown("Your AI-powered assistant for stock market information and company details")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Keys input
    finnhub_api_key = st.text_input("Finnhub API Key", type="password", value="d87h1n1r01qmhakfpangd87h1n1r01qmhakfpanao")
    alpha_vantage_api_key = st.text_input("Alpha Vantage API Key", type="password", value="EXKT5UJD09F47WBW")
    
    # Model configuration
    model_name = st.selectbox(
        "Select Model",
        ["openai/gpt-oss-120b", "mixtral-8x7b-32768", "llama3-70b-8192"],
        index=0
    )
    temperature = st.slider("Temperature", 0.0, 2.0, 1.5, 0.1)
    
    st.divider()
    
    # Example stocks
    st.subheader("📌 Example Stocks")
    st.markdown("**Indian Stocks (BSE):**\n- TCS.BSE\n- RELIANCE.BSE\n- INFY.BSE\n- HDFCBANK.BSE")
    st.markdown("**US Stocks:**\n- AAPL\n- TSLA\n- NVDA\n- MSFT")

# Initialize the model and tools
@st.cache_resource
def initialize_agent(finnhub_key, alpha_vantage_key, model_name, temperature):
    # Update API keys in tool functions
    def create_tools():
        @tool
        def get_stock_price(symbol: str):
            """
            Get live stock price using Finnhub API.
            Example: AAPL, TSLA, NVDA
            """
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={finnhub_key}"
            response = requests.get(url)
            data = response.json()
            
            if 'c' not in data:
                return f"Error: Could not fetch data for {symbol}. Please check the symbol."
            
            return f"""
📊 Stock: {symbol}

💰 Current Price: ${data['c']}
📈 High Price: ${data['h']}
📉 Low Price: ${data['l']}
🔓 Open Price: ${data['o']}
📅 Previous Close: ${data['pc']}
            """
        
        @tool
        def get_indian_stock_price(symbol: str):
            """
            Get Indian stock market price.
            Example: RELIANCE.BSE, TCS.BSE, INFY.BSE
            """
            url = (f"https://www.alphavantage.co/query?"
                   f"function=GLOBAL_QUOTE"
                   f"&symbol={symbol}"
                   f"&apikey={alpha_vantage_key}")
            
            response = requests.get(url)
            data = response.json()
            
            try:
                quote = data["Global Quote"]
                return f"""
📊 Stock: {symbol}

💰 Current Price: ₹{quote['05. price']}
🔓 Open Price: ₹{quote['02. open']}
📈 High Price: ₹{quote['03. high']}
📉 Low Price: ₹{quote['04. low']}
📅 Previous Close: ₹{quote['08. previous close']}
📊 Volume: {quote['06. volume']}
📈 Change Percent: {quote['10. change percent']}
                """
            except Exception as e:
                return f"Error fetching stock data for {symbol}: {str(e)}"
        
        @tool
        def get_indian_stock_details(symbol: str):
            """
            Get detailed information about Indian stocks.
            Example: RELIANCE.BSE, TCS.BSE, INFY.BSE
            """
            # First get the price
            url_price = (f"https://www.alphavantage.co/query?"
                        f"function=GLOBAL_QUOTE"
                        f"&symbol={symbol}"
                        f"&apikey={alpha_vantage_key}")
            
            response = requests.get(url_price)
            data = response.json()
            
            company_name = symbol.split('.')[0]
            
            return f"""
🏢 Company: {company_name}
📊 Stock Symbol: {symbol}

📋 Company Details for {company_name}:
This is a prominent company in the Indian stock market. For detailed financial reports and company information, please visit the official company website or financial portals like Moneycontrol, Economic Times, or BSE India.

Current Market Status:
{data.get('Global Quote', {})}
            """
        
        @tool
        def get_usa_stock_details(symbol: str):
            """
            Get detailed information about US stocks.
            Example: AAPL, TSLA, NVDA
            """
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={finnhub_key}"
            response = requests.get(url)
            data = response.json()
            
            return f"""
🏢 Company: {symbol}
📊 Stock Symbol: {symbol}

📋 Company Details for {symbol}:
{symbol} is a publicly traded company on US stock exchanges. For comprehensive company information including financial statements, SEC filings, and business overview, please visit Yahoo Finance, Bloomberg, or the company's investor relations website.

Current Market Data:
Current Price: ${data.get('c', 'N/A')}
Day High: ${data.get('h', 'N/A')}
Day Low: ${data.get('l', 'N/A')}
            """
        
        return [get_stock_price, get_indian_stock_price, get_indian_stock_details, get_usa_stock_details]
    
    # Initialize model
    model = ChatGroq(
        model=model_name,
        temperature=temperature,
        api_key=st.secrets.get("GROQ_API_KEY", "")  # You can also use secrets
    )
    
    # Create agent
    prompt = """You are an expert stock market advisor. Provide comprehensive information about stocks including current price, high, low, previous close, open price, and company details. Be helpful and accurate in your responses."""
    
    agent = create_react_agent(
        model=model,
        tools=create_tools(),
        prompt=prompt
    )
    
    return agent

# Main chat interface
def main():
    # Initialize session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "agent" not in st.session_state:
        st.session_state.agent = None
    
    # Initialize agent if API keys are provided
    finnhub_key = st.sidebar.text_input("Finnhub API Key", type="password", value="d87h1n1r01qmhakfpangd87h1n1r01qmhakfpanao", key="finnhub_input")
    alpha_key = st.sidebar.text_input("Alpha Vantage API Key", type="password", value="EXKT5UJD09F47WBW", key="alpha_input")
    model_name = st.sidebar.selectbox("Select Model", ["openai/gpt-oss-120b", "mixtral-8x7b-32768", "llama3-70b-8192"], key="model_select")
    temperature = st.sidebar.slider("Temperature", 0.0, 2.0, 1.5, 0.1, key="temp_slider")
    
    if finnhub_key and alpha_key:
        if st.session_state.agent is None:
            with st.spinner("Initializing Stock Market Advisor Agent..."):
                st.session_state.agent = initialize_agent(finnhub_key, alpha_key, model_name, temperature)
            st.success("Agent initialized successfully!")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask about stock prices, company details, or market information..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get agent response
            with st.chat_message("assistant"):
                with st.spinner("Analyzing market data..."):
                    try:
                        response = st.session_state.agent.invoke({'input': prompt})
                        assistant_response = response["messages"][-1].content
                        st.markdown(assistant_response)
                        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                    except Exception as e:
                        error_msg = f"Error: {str(e)}. Please check your API keys and try again."
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    else:
        st.warning("⚠️ Please enter your API keys in the sidebar to start using the Stock Market Advisor Agent.")
        
        # Show demo information
        st.info("""
        ### How to get API Keys:
        
        **Finnhub API Key (for US stocks):**
        1. Visit [Finnhub](https://finnhub.io/)
        2. Sign up for a free account
        3. Get your API key from the dashboard
        
        **Alpha Vantage API Key (for Indian stocks):**
        1. Visit [Alpha Vantage](https://www.alphavantage.co/)
        2. Sign up for a free API key
        3. Use your key in the sidebar
        
        **Groq API Key:**
        1. Visit [Groq Console](https://console.groq.com/)
        2. Sign up and get your API key
        3. Add it to your Streamlit secrets or environment variables
        """)

if __name__ == "__main__":
    main()
