import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta
import pytz
from io import StringIO

# Page configuration
st.set_page_config(
    page_title="Stock Interval Price Calculator",
    page_icon="📈",
    layout="wide"
)
#Welcome to Alpha Vantage! Here is your API key: Y6DF2DE208C7HXHE. Please record this API key at a safe place for future data access.


# Alpha Vantage API configuration
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "YourKey")
BASE_URL = "https://www.alphavantage.co/query"

def validate_symbol(symbol):
    """Validate stock/ETF symbol format"""
    if not symbol:
        return False
    # Basic validation: alphanumeric, 1-5 characters
    return symbol.isalpha() and 1 <= len(symbol) <= 5

def fetch_intraday_data(symbol):
    """Fetch intraday data from Alpha Vantage API"""
    params = {
        'function': 'TIME_SERIES_INTRADAY',
        'symbol': symbol,
        'interval': '5min',
        'outputsize': 'full',
        'apikey': API_KEY
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if "Error Message" in data:
            st.error(f"API Error: {data['Error Message']}")
            return None
        
        if "Note" in data:
            st.error("API call frequency limit reached. Please try again later.")
            return None
            
        if "Information" in data:
            st.error("API rate limit exceeded. Please wait before making another request.")
            return None
        
        # Check if we have time series data
        time_series_key = "Time Series (5min)"
        if time_series_key not in data:
            st.error(f"No intraday data found for symbol: {symbol}. Please check if the symbol is valid.")
            return None
            
        return data[time_series_key]
        
    except requests.exceptions.RequestException as e:
        st.error(f"Network error occurred: {str(e)}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return None

def process_data_for_intervals(data, symbol):
    """Process the fetched data and calculate averages for specified intervals"""
    if not data:
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame.from_dict(data, orient='index')
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    # Convert price columns to float
    price_columns = ['Open', 'High', 'Low', 'Close']
    for col in price_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Convert index to datetime and set timezone to EST
    df.index = pd.to_datetime(df.index)
    df.index = df.index.tz_localize('UTC').tz_convert('US/Eastern')
    
    # Filter for the past 7 days (trading days only)
    end_date = datetime.now(pytz.timezone('US/Eastern'))
    start_date = end_date - timedelta(days=10)  # Go back 10 days to ensure we get 7 trading days
    
    df = df[(df.index >= start_date) & (df.index <= end_date)]
    
    if df.empty:
        st.warning("No data available for the past 7 days.")
        return None
    
    # Define time intervals
    intervals = {
        'Morning (9:00-9:35 AM)': ('09:00', '09:35'),
        'Mid-Morning (11:00-11:30 AM)': ('11:00', '11:30'),
        'Market Close (3:30-4:00 PM)': ('15:30', '16:00')
    }
    
    # Calculate averages for each day and interval
    results = []
    
    # Group by date
    df['Date'] = df.index.date
    grouped = df.groupby('Date')
    
    for date, day_data in grouped:
        # Skip weekends
        if pd.to_datetime(date).weekday() >= 5:
            continue
            
        row = {'Date': date.strftime('%Y-%m-%d'), 'Day': pd.to_datetime(date).strftime('%A')}
        
        for interval_name, (start_time, end_time) in intervals.items():
            # Filter data for the specific time interval
            interval_data = day_data.between_time(start_time, end_time)
            
            if not interval_data.empty:
                # Calculate average of OHLC prices
                avg_price = interval_data[price_columns].mean().mean()
                row[interval_name] = round(avg_price, 2)
            else:
                row[interval_name] = "No Data"
        
        results.append(row)
    
    # Convert to DataFrame and sort by date (most recent first)
    results_df = pd.DataFrame(results)
    if not results_df.empty:
        results_df['Date'] = pd.to_datetime(results_df['Date'])
        results_df = results_df.sort_values('Date', ascending=False)
        results_df['Date'] = results_df['Date'].dt.strftime('%Y-%m-%d')
    
    return results_df

def export_to_csv(df, symbol):
    """Convert DataFrame to CSV for download"""
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

def main():
    st.title("📈 Stock/ETF Interval Price Calculator")
    st.markdown("Calculate average prices for specific trading intervals over the past 7 days")
    
    # Sidebar for input
    with st.sidebar:
        st.header("Configuration")
        
        # Symbol input
        symbol = st.text_input(
            "Enter Stock/ETF Symbol:",
            placeholder="e.g., AAPL, SPY, QQQ",
            help="Enter a valid stock or ETF symbol (1-5 letters)"
        ).upper().strip()
        
        # Information about intervals
        st.subheader("Trading Intervals (EST):")
        st.write("• **Morning**: 9:00-9:35 AM")
        st.write("• **Mid-Morning**: 11:00-11:30 AM")
        st.write("• **Market Close**: 3:30-4:00 PM")
        
        # Calculate button
        calculate_clicked = st.button("Calculate Averages", type="primary")
    
    # Main content area
    if calculate_clicked:
        if not validate_symbol(symbol):
            st.error("Please enter a valid stock/ETF symbol (1-5 letters, alphabetic characters only)")
            return
        
        # Show loading message
        with st.spinner(f"Fetching intraday data for {symbol}..."):
            # Fetch data
            raw_data = fetch_intraday_data(symbol)
        
        if raw_data:
            with st.spinner("Processing data and calculating interval averages..."):
                # Process data
                results_df = process_data_for_intervals(raw_data, symbol)
            
            if results_df is not None and not results_df.empty:
                st.success(f"Successfully calculated interval averages for {symbol}")
                
                # Display results
                st.subheader(f"Average Prices for {symbol} - Past 7 Trading Days")
                
                # Format the dataframe for better display
                display_df = results_df.copy()
                
                # Style numeric columns
                def format_price(val):
                    if isinstance(val, (int, float)):
                        return f"${val:.2f}"
                    return val
                
                # Apply formatting to price columns
                price_columns = ['Morning (9:00-9:35 AM)', 'Mid-Morning (11:00-11:30 AM)', 'Market Close (3:30-4:00 PM)']
                for col in price_columns:
                    if col in display_df.columns:
                        display_df[col] = display_df[col].apply(format_price)
                
                # Display the table
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Summary statistics
                st.subheader("Summary Statistics")
                
                col1, col2, col3 = st.columns(3)
                
                # Calculate overall averages for each interval
                numeric_df = results_df.copy()
                for col in price_columns:
                    if col in numeric_df.columns:
                        numeric_df[col] = pd.to_numeric(numeric_df[col], errors='coerce')
                
                with col1:
                    morning_avg = numeric_df['Morning (9:00-9:35 AM)'].mean()
                    if not pd.isna(morning_avg):
                        st.metric("7-Day Morning Average", f"${morning_avg:.2f}")
                    else:
                        st.metric("7-Day Morning Average", "No Data")
                
                with col2:
                    midmorning_avg = numeric_df['Mid-Morning (11:00-11:30 AM)'].mean()
                    if not pd.isna(midmorning_avg):
                        st.metric("7-Day Mid-Morning Average", f"${midmorning_avg:.2f}")
                    else:
                        st.metric("7-Day Mid-Morning Average", "No Data")
                
                with col3:
                    close_avg = numeric_df['Market Close (3:30-4:00 PM)'].mean()
                    if not pd.isna(close_avg):
                        st.metric("7-Day Market Close Average", f"${close_avg:.2f}")
                    else:
                        st.metric("7-Day Market Close Average", "No Data")
                
                # Export functionality
                st.subheader("Export Data")
                csv_data = export_to_csv(results_df, symbol)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"{symbol}_interval_averages_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
                
            else:
                st.warning("No trading data available for the specified symbol in the past 7 days.")
    
    else:
        # Show instructions when no calculation has been performed
        st.info("👈 Enter a stock or ETF symbol in the sidebar and click 'Calculate Averages' to get started.")
        
        # Show example
        st.subheader("How it works:")
        st.write("""
        1. **Enter Symbol**: Input any valid stock or ETF symbol (e.g., AAPL, SPY, QQQ)
        2. **Fetch Data**: The app retrieves 5-minute intraday data for the past 7 trading days
        3. **Calculate Averages**: For each trading day, it calculates the average price during:
           - Morning session (9:00-9:35 AM EST)
           - Mid-morning session (11:00-11:30 AM EST)  
           - Market close session (3:30-4:00 PM EST)
        4. **View Results**: See the results in a clear table with summary statistics
        5. **Export**: Download the data as a CSV file for further analysis
        """)
        
        st.subheader("Notes:")
        st.write("""
        - All times are in Eastern Standard Time (EST)
        - Only trading days are included (weekends are excluded)
        - Market holidays may result in missing data
        - Data is sourced from Alpha Vantage API
        - Average prices are calculated from Open, High, Low, and Close values within each interval
        """)

if __name__ == "__main__":
    main()
