# 📈 StockIntervalPriceCalculator

A simple tool to **calculate average prices for stocks or ETFs over specific trading intervals**—including the past 7 days.

## 🚀 Features

- Calculate average prices for any stock or ETF over customizable intervals (default: past 7 days)
- User-friendly sidebar for quick symbol entry
- Fast results with a single click

## 🛠️ Getting Started

### 1. Enter a Symbol

- Input any valid stock or ETF symbol (e.g., `AAPL`, `SPY`, `QQQ`) in the sidebar.

### 2. Calculate Averages

- Click **'Calculate Averages'** to view average prices for your selected interval.

## 🏗️ Building & Running

### Build with Docker

```bash
docker build -t StockIntervalPriceCalculator .
```

### Run the App

```bash
docker run -p 8501:8501 StockIntervalPriceCalculator
```

Then open your browser and navigate to `http://localhost:8501`.

## 💡 How It Works

1. **Enter Symbol:** Type a valid stock or ETF ticker in the sidebar.
2. **Calculate:** Click the button to fetch and display average interval prices for the last 7 days.
3. **Review:** Instantly see the results in a clear, tabular format.

## 📋 Example

- To calculate the average price for Apple Inc. over the past week:
  1. Enter `AAPL` in the sidebar
  2. Click **'Calculate Averages'**
  3. View the results displayed below

For more information or to contribute, please see the [CONTRIBUTING.md] or open an issue.
 
