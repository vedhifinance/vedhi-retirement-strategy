# Vedhi Finance — Retirement Strategy Dashboard

A conservative retirement strategy tracker built with Streamlit.

## Strategy Rules

| Rule | Detail |
|------|--------|
| Treasury split | 40% Liquidcase ETF · 60% Equity pool |
| Liquidcase yield | 5–6% per year |
| Entry — Tranche 1 | RSI 35–40 · EMA 20–50 · Volume rising · Last candle green |
| Entry — Tranche 2 | Stock falls 7% from T1 buy price |
| Max position | 10% of equity pool per trade |
| Stop loss | 2% below buy rate |
| Profit target | Minimum 4% then trailing stop |
| Risk : Reward | 1 : 2 |

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account → select this repo → `app.py` → Deploy

> **Note:** Streamlit Cloud does not persist session data between restarts.
> Use the **Import / Export CSV** buttons in Treasury and Trades tabs to save and reload your data.
