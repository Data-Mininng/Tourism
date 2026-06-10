import pandas as pd
from sklearn.preprocessing import MinMaxScaler

def tien_xu_ly_data_that(file_vao, file_ra):
    # 1. Đọc file CSV tải từ mạng về
    df = pd.read_csv(file_vao)
    
    # 2. Tạo nhãn quyết định Voucher: Nếu lượn lờ nhiều (PageValues > 0) mà KHÔNG mua (Revenue == False)
    df['Need_Voucher'] = ((df['PageValues'] > 0) & (df['Revenue'] == False)).astype(int)
    
    # 3. Lọc lấy các cột thao tác web cốt lõi để train
    cac_cot_giu_lai = ['Administrative_Duration', 'Informational_Duration', 'ProductRelated_Duration', 
                       'BounceRates', 'ExitRates', 'PageValues', 'Weekend', 'Need_Voucher']
    df = df[cac_cot_giu_lai]
    
    # Mã hóa cột Weekend (True/False -> 1/0)
    df['Weekend'] = df['Weekend'].astype(int)
    
    # 4. Chuẩn hóa Min-Max cho các cột thời gian số học
    scaler = MinMaxScaler()
    cot_so_hoc = ['Administrative_Duration', 'Informational_Duration', 'ProductRelated_Duration', 'BounceRates', 'ExitRates', 'PageValues']
    df[cot_so_hoc] = scaler.fit_transform(df[cot_so_hoc])
    
    # 5. Xuất file sạch để đưa vào File 3 train thuật toán
    df.to_csv(file_ra, index=False)
    print("Đã tiền xử lý xong data thật từ Internet! Sẵn sàng để huấn luyện.")

if __name__ == "__main__":
    # Giả sử anh tải về đổi tên file thành data_mang.csv
    tien_xu_ly_data_that('online_shoppers_intention.csv', 'du_lieu_da_xu_ly.csv')