#!/usr/bin/env python
# coding: utf-8

# In[ ]:





# In[ ]:


import statsmodels.api as sm
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

# Định nghĩa danh sách các mã cổ phiếu cần xử lý
stock_symbols = ["ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE"]  # Thêm các mã cổ phiếu bạn muốn vào đây

# Tạo giao diện người dùng cho việc tải tệp
uploaded_file_vnindex = st.file_uploader("Chọn tệp dữ liệu VN-Index", type=["xlsx"])
uploaded_files_stock = {symbol: st.file_uploader(f"Chọn tệp dữ liệu cổ phiếu {symbol}", type=["xlsx"]) for symbol in stock_symbols}

# Kiểm tra nếu người dùng đã tải tệp lên
if uploaded_file_vnindex is not None:
    df_vnindex = pd.read_excel(uploaded_file_vnindex)

    # Lọc dữ liệu từ năm 2019 trở đi
    df_vnindex['time'] = pd.to_datetime(df_vnindex['time'])
    df_vnindex = df_vnindex[df_vnindex['time'].dt.year >= 2019]

    # Khởi tạo danh sách để lưu kết quả Alpha và Beta gần nhất
    ranking_data = []

    # Tạo một figure cho biểu đồ
    plt.figure(figsize=(14, 10))

    # Xử lý từng mã cổ phiếu
    for stock_symbol, uploaded_file in uploaded_files_stock.items():
        if uploaded_file is not None:
            df_symbols = pd.read_excel(uploaded_file)

            # Đảm bảo rằng cột time trong cả hai DataFrame có kiểu dữ liệu datetime
            df_symbols['time'] = pd.to_datetime(df_symbols['time'])
            df_vnindex['time'] = pd.to_datetime(df_vnindex['time'])

            # Lọc dữ liệu từ năm 2019 trở đi cho cổ phiếu
            df_symbols = df_symbols[df_symbols['time'].dt.year >= 2019]

            # Ghép dữ liệu dựa vào cột time
            merged_df = pd.merge(df_symbols, df_vnindex, on='time', how='inner')

            # Xoá các hàng chứa giá trị NaN
            merged_df.dropna(inplace=True)

            # Tính toán return từ cột close (lợi nhuận cổ phiếu và VN-Index)
            merged_df['return_stock'] = merged_df['close_x'].pct_change()  # Lợi nhuận cổ phiếu
            merged_df['return_vnindex'] = merged_df['close_y'].pct_change()  # Lợi nhuận VN-Index

            # Tính Alpha và Beta bằng hồi quy tuyến tính
            betas = []
            alphas = []
            dates = []

            # Thực hiện hồi quy với cửa sổ 30 ngày
            window = 30
            for i in range(window, len(merged_df)):
                # Lấy dữ liệu của 30 ngày trước
                window_data = merged_df.iloc[i-window:i]

                # Lấy lợi nhuận cổ phiếu và VN-Index
                y = window_data['return_stock']
                X = window_data['return_vnindex']

                # Kiểm tra và loại bỏ bất kỳ giá trị NaN hoặc Inf trong X và y
                if y.isnull().any() or X.isnull().any() or (y == float('inf')).any() or (X == float('inf')).any():
                    continue  # Bỏ qua dòng này nếu có NaN hoặc Inf

                # Thêm cột constant (hằng số) cho hồi quy
                X = sm.add_constant(X)

                # Hồi quy tuyến tính
                model = sm.OLS(y, X).fit()

                # Lấy Alpha và Beta (Alpha là hệ số intercept, Beta là hệ số của VN-Index)
                alpha = model.params[0]  # Hệ số của intercept (Alpha)
                beta = model.params[1]   # Hệ số của VN-Index (Beta)
                p_value = model.pvalues[1]  # Lấy p-value của Beta

                # Chỉ lưu Alpha và Beta nếu p-value < 0.05 (Có ý nghĩa thống kê)
                if p_value < 0.05:
                    betas.append(beta)
                    alphas.append(alpha)
                    dates.append(merged_df['time'].iloc[i])

            # Lưu Alpha và Beta gần nhất của cổ phiếu vào danh sách
            if alphas and betas:  # Kiểm tra nếu có giá trị Alpha và Beta
                latest_alpha = alphas[-1]
                latest_beta = betas[-1]
                ranking_data.append([stock_symbol, latest_alpha, latest_beta])

            # Vẽ biểu đồ Beta và Alpha cho từng mã cổ phiếu
            # Biểu đồ Beta
            plt.subplot(len(stock_symbols), 2, 2*stock_symbols.index(stock_symbol) + 1)
            plt.plot(dates, betas, label=f'Beta ({stock_symbol})', color='blue')
            plt.title(f'Biểu đồ Beta của cổ phiếu {stock_symbol} so với VN-Index')
            plt.xlabel('Ngày')
            plt.ylabel('Beta')
            plt.legend()
            plt.grid(True)

            # Biểu đồ Alpha
            plt.subplot(len(stock_symbols), 2, 2*stock_symbols.index(stock_symbol) + 2)
            plt.plot(dates, alphas, label=f'Alpha ({stock_symbol})', color='green')
            plt.title(f'Biểu đồ Alpha của cổ phiếu {stock_symbol} so với VN-Index')
            plt.xlabel('Ngày')
            plt.ylabel('Alpha')
            plt.legend()
            plt.grid(True)

    # Chuyển danh sách xếp hạng thành DataFrame
    ranking_df = pd.DataFrame(ranking_data, columns=['Mã cổ phiếu', 'Alpha', 'Beta'])

    # Sắp xếp bảng xếp hạng theo Alpha từ lớn đến nhỏ
    ranking_df = ranking_df.sort_values(by='Alpha', ascending=False)

    # Đặt lại chỉ số bắt đầu từ 1
    ranking_df.reset_index(drop=True, inplace=True)
    ranking_df.index += 1  # Đặt chỉ số bắt đầu từ 1

    # Hiển thị bảng xếp hạng
    st.dataframe(ranking_df)

    # Hiển thị biểu đồ với Streamlit
    plt.tight_layout()
    st.pyplot()
else:
    st.warning("Vui lòng tải tệp dữ liệu VN-Index và các tệp cổ phiếu.")



# In[ ]:




