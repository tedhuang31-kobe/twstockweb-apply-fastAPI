import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 網頁配置
st.set_page_config(page_title="專業股價分析系統", layout="wide")
st.title("📈 股價技術分析儀表板 (FastAPI + Streamlit)")

# 側邊欄：使用者輸入
st.sidebar.header("查詢設定")
stock_id = st.sidebar.text_input("輸入股票代碼 (台股請加 .TW)", value="2330.TW")
period_options = {"半年": "6mo", "一年": "1y", "兩年": "2y"}
selected_label = st.sidebar.selectbox("時間範圍", options=list(period_options.keys()))
selected_period = period_options[selected_label]

if st.sidebar.button("開始分析"):
    with st.spinner('連線至後端抓取資料中...'):
        try:
            # 呼叫後端 API
            response = requests.get(f"http://127.0.0.1:8000/stock/{stock_id}?period={selected_period}")
            
            if response.status_code == 200:
                df = pd.DataFrame(response.json())
                
                # --- 1. 繪製三層互動圖表 ---
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                    vertical_spacing=0.05, 
                                    subplot_titles=('K線走勢', '成交量', 'KD 指標 (9,3,3)'),
                                    row_heights=[0.5, 0.2, 0.3])

                # 主圖：K線圖
                fig.add_trace(go.Candlestick(
                    x=df['日期'], open=df['開盤價'], high=df['最高價'], 
                    low=df['最低價'], close=df['收盤價'], name='K線'
                ), row=1, col=1)

                # 中間：成交量
                fig.add_trace(go.Bar(
                    x=df['日期'], y=df['成交量'], name='成交量', marker_color='orange', opacity=0.7
                ), row=2, col=1)

                # 下方：KD 指標
                fig.add_trace(go.Scatter(x=df['日期'], y=df['K值'], name='K值 (快線)', line=dict(color='blue')), row=3, col=1)
                fig.add_trace(go.Scatter(x=df['日期'], y=df['D值'], name='D值 (慢線)', line=dict(color='red')), row=3, col=1)
                
                # 加入 20/80 基準線
                fig.add_hline(y=80, line_dash="dash", line_color="gray", row=3, col=1)
                fig.add_hline(y=20, line_dash="dash", line_color="gray", row=3, col=1)

                fig.update_layout(height=800, xaxis_rangeslider_visible=False, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)

                # --- 2. 自動診斷區塊 ---
                st.subheader("🔍 技術面分析診斷")
                latest_k = df['K值'].iloc[-1]
                latest_d = df['D值'].iloc[-1]

                col1, col2 = st.columns(2)
                col1.metric("當前 K值 (快線)", f"{latest_k:.2f}")
                col2.metric("當前 D值 (慢線)", f"{latest_d:.2f}")

                if latest_k > latest_d and latest_k < 25:
                    st.success("💡 **低檔黃金交叉**：目前 K值 處於低檔且向上突破 D值，是潛在的買進訊號！")
                elif latest_k < latest_d and latest_k > 75:
                    st.warning("⚠️ **高檔死亡交叉**：目前 K值 處於高檔且向下跌破 D值，請注意回檔風險或適時獲利結清。")
                else:
                    st.info(f"📊 **目前盤勢觀望**：KD 數值尚未進入極端區域，建議配合量能表現持續觀察。")

                # --- 3. 數據明細表格 ---
                st.subheader("📋 歷史數據明細")
                st.dataframe(df.tail(30), use_container_width=True)

            else:
                st.error(f"無法取得資料。錯誤代碼: {response.status_code}")
        except Exception as e:
            st.error(f"連線失敗，請確認後端 api.py 是否正在運行。詳細訊息: {e}")