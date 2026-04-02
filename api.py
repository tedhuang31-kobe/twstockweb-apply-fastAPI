from fastapi import FastAPI, HTTPException
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import uvicorn
import numpy as np

app = FastAPI()

@app.get("/stock/{ticker}")
def get_stock_data(ticker: str, period: str = "1y"):
    try:
        # 1. 抓取資料
        df = yf.download(ticker, period=period)
        if df.empty:
            raise HTTPException(status_code=404, detail="找不到股票代碼")

        # 處理 yfinance 可能產生的 MultiIndex 欄位 (扁平化)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 2. 計算 KD 指標 (Stochastic Oscillator)
        kd = df.ta.stoch(high='High', low='Low', close='Close', k=9, d=3, smooth_k=3)
        
        # 3. 合併資料並處理空值 (避免 JSON 報錯)
        df = pd.concat([df, kd], axis=1)
        df = df.fillna(0).replace([np.inf, -np.inf], 0)
        
        # 4. 重置索引並轉換日期格式
        df.reset_index(inplace=True)
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

        # 5. 欄位翻譯與過濾 (移除不需要的 STOCHh 等中間數據)
        column_map = {
            'Date': '日期',
            'Open': '開盤價',
            'High': '最高價',
            'Low': '最低價',
            'Close': '收盤價',
            'Volume': '成交量',
            'STOCHk_9_3_3': 'K值',
            'STOCHd_9_3_3': 'D值'
        }
        
        # 只保留定義好的欄位並更名
        df = df[column_map.keys()].rename(columns=column_map)
        
        return df.to_dict(orient='records')
        
    except Exception as e:
        print(f"後端發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)