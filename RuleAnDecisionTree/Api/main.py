from fastapi import FastAPI, Query
from pydantic import BaseModel
import uvicorn
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
import os
import joblib
import numpy as np
from sklearn.tree import export_text
import database
import rule_generator

app = FastAPI()

# Cấu hình CORS đồng bộ cổng kết nối an toàn với .NET
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các nguồn gọi tới
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Bắt buộc phải có OPTIONS
    allow_headers=["*"],
)

# =====================================================================
# 1. ĐỊNH NGHĨA CẤU TRÚC DỮ LIỆU ĐẦU VÀO (PYDANTIC SCHEMAS)
# =====================================================================

class RuleParams(BaseModel):
    min_support: float = 0.1
    min_confidence: float = 0.5


class VoucherPredictParams(BaseModel):
    administrative_duration: float
    informational_duration: float
    productrelated_duration: float
    bounce_rates: float
    exit_rates: float
    page_values: float
    weekend: int  # Đảm bảo nhận dạng số (1/0) hoặc ép kiểu mượt mà từ .NET sang


# =====================================================================
# 2. KHỞI TẠO VÀ TỰ ĐỘNG NẠP MÔ HÌNH HỌC MÁY (VOUCHER MODEL)
# =====================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Đồng bộ hóa chính xác tên file lưu trữ scaler thực tế trong Dataset của bạn
VOUCHER_DIR = os.path.join(BASE_DIR, "..", "Dataset", "Voucher")

voucher_model = None
voucher_scaler = None

# Thử nạp file mô hình học máy và bộ chuẩn hóa đặc trưng
try:
    model_path = os.path.join(VOUCHER_DIR, "mo_hinh_quyet_dinh_voucher.pkl")
    # Kiểm tra cả tên file 'scaler_voucher.pkl' hoặc 'bo_chuan_hoa_voucher.pkl' tùy hệ thống lưu
    scaler_path = os.path.join(VOUCHER_DIR, "scaler_voucher.pkl")
    if not os.path.exists(scaler_path):
        scaler_path = os.path.join(VOUCHER_DIR, "bo_chuan_hoa_voucher.pkl")

    voucher_model = joblib.load(model_path)
    voucher_scaler = joblib.load(scaler_path)
    print("✅ Đã load mô hình và scaler từ thư mục Dataset thành công!")
except Exception as e:
    voucher_model = None
    voucher_scaler = None
    print(f"⚠️ Cảnh báo: Không thể nạp tệp mô hình hoặc bộ chuẩn hóa: {e}")


# =====================================================================
# 3. ENDPOINT XỬ LÝ HỆ THỐNG GỢI Ý LUẬT (FP-GROWTH)
# =====================================================================

@app.post("/api/train-rules")
def train_rules_endpoint(params: RuleParams):
    try:
        # Bước 1: Gọi DB lấy Data
        df_transactions = database.get_transactions()

        # Bước 2: Ném Data vào lò AI luyện ra Luật
        df_rules = rule_generator.run_fpgrowth(df_transactions, params.min_support, params.min_confidence)

        # Bước 3: Ném Luật về lại DB để lưu
        database.save_rules(df_rules)

        return {
            "status": "success", 
            "message": "Cập nhật luật thành công tuyệt đối!",
            "total_rules_generated": len(df_rules)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/recommendations")
def get_recommendations(service_name: str = Query(None), limit: int = 3):
    try:
        if not service_name or service_name.strip() == "":
            return {"status": "success", "data": []}

        # Bốc mớ hành vi vết lướt từ JavaScript/C# gửi sang biến thành set tập hợp và dọn khoảng trắng
        current_user_behaviors = set([b.strip() for b in service_name.split(",") if b.strip()])

        # Lấy bảng luật lên từ SQL Server (Bọc dự phòng trường hợp tên bảng viết liền/viết cách)
        try:
            query = "SELECT DichVu_Goc, DichVu_GoiY, Do_Tin_Cay_Confidence FROM Luat_FPGrowth"
            df_rules = pd.read_sql(query, database.engine)
        except Exception:
            query = "SELECT DichVu_Goc, DichVu_GoiY, Do_Tin_Cay_Confidence FROM LuatFPGrowth"
            df_rules = pd.read_sql(query, database.engine)

        if df_rules.empty:
            return {"status": "success", "data": []}

        valid_rules = []

        for index, row in df_rules.iterrows():
            # SỬA LỖI CHÍ MẠNG: Dọn dẹp khoảng trắng thừa của từng item vế trái bốc lên từ Database (tránh bẫy ", ")
            db_rule_antecedent = set([item.strip() for item in str(row['DichVu_Goc']).split(",") if item.strip()])

            # Kiểm tra xem tổ hợp lướt web hiện tại của khách có chứa trọn vế gốc của luật này không
            if db_rule_antecedent and db_rule_antecedent.issubset(current_user_behaviors):
                
                # Loại bỏ không gợi ý lại những gì khách ĐÃ lướt qua hoặc đang xem
                v_phai_items = [i.strip() for i in str(row['DichVu_GoiY']).split(",") if i.strip()]
                if not any(item in current_user_behaviors for item in v_phai_items):
                    valid_rules.append({
                        "DichVu_Goc": str(row['DichVu_Goc']).strip(),
                        "DichVu_GoiY": str(row['DichVu_GoiY']).strip(),
                        "Do_Tin_Cay_Confidence": float(row['Do_Tin_Cay_Confidence'])
                    })

        if len(valid_rules) > 0:
            df_result = pd.DataFrame(valid_rules)
            # Sắp xếp confidence giảm dần
            df_result = df_result.sort_values(by="Do_Tin_Cay_Confidence", ascending=False)
            # Gom nhóm loại trùng vế gợi ý, chỉ giữ lại dòng luật có độ tin cậy tối ưu nhất
            df_result = df_result.groupby("DichVu_GoiY").first().reset_index()
            df_result = df_result.sort_values(by="Do_Tin_Cay_Confidence", ascending=False).head(limit)
            
            return {"status": "success", "data": df_result.to_dict(orient="records")}
        
        return {"status": "success", "data": []}

    except Exception as e:
        return {"status": "error", "message": f"Lỗi xử lý gợi ý hệ thống: {str(e)}"}


# =====================================================================
# 4. ENDPOINT DỰ ĐOÁN TẶNG VOUCHER (DECISION TREE)
# =====================================================================

from fastapi import HTTPException # Nhớ kiểm tra xem đã import chưa ở đầu file

@app.post("/api/predict-voucher")
def predict_voucher_endpoint(params: VoucherPredictParams):
    try:
        if voucher_model is None or voucher_scaler is None:
            return {
                "need_voucher": 0, 
                "discount_percent": 0, 
                "error": "Mô hình hoặc Bộ chuẩn hóa chưa được nạp thành công lên máy chủ Python."
            }

        # Gom toàn bộ dữ liệu đầu vào cấu hình thành một map bản đồ dữ liệu chữ thường sạch sẽ
        param_mapping = {
            "administrative_duration": params.administrative_duration,
            "informational_duration": params.informational_duration,
            "productrelated_duration": params.productrelated_duration,
            "bounce_rates": params.bounce_rates,
            "exit_rates": params.exit_rates,
            "page_values": params.page_values,
            "weekend": 1 if params.weekend else 0
        }
        clean_param_map = {k.lower().replace("_", ""): v for k, v in param_mapping.items()}

        # Căn chỉnh khít thứ tự cột yêu cầu của Bộ chuẩn hóa Scaler
        if hasattr(voucher_scaler, "feature_names_in_"):
            scaler_features = list(voucher_scaler.feature_names_in_)
            aligned_scaler_data = {}
            for col in scaler_features:
                clean_col_name = col.lower().replace("_", "")
                aligned_scaler_data[col] = clean_param_map.get(clean_col_name, 0.0)
            input_df = pd.DataFrame([aligned_scaler_data])
            numeric_scaled = voucher_scaler.transform(input_df)
        else:
            numeric_features = np.array([[
                params.administrative_duration, params.informational_duration,
                params.productrelated_duration, params.bounce_rates,
                params.exit_rates, params.page_values
            ]])
            numeric_scaled = voucher_scaler.transform(numeric_features)

        # Căn chỉnh khít thứ tự cột yêu cầu của Mô hình học máy Cây quyết định (Decision Tree)
        if hasattr(voucher_model, "feature_names_in_"):
            model_features = list(voucher_model.feature_names_in_)
            aligned_model_data = {}
            for col in model_features:
                clean_col_name = col.lower().replace("_", "")
                if hasattr(voucher_scaler, "feature_names_in_") and col in list(voucher_scaler.feature_names_in_):
                    idx = list(voucher_scaler.feature_names_in_).index(col)
                    aligned_model_data[col] = numeric_scaled[0][idx]
                else:
                    aligned_model_data[col] = clean_param_map.get(clean_col_name, 0)
            final_df = pd.DataFrame([aligned_model_data])
            prediction = voucher_model.predict(final_df)
        else:
            weekend_val = 1 if params.weekend else 0
            final_features = np.hstack((numeric_scaled, [[weekend_val]]))
            prediction = voucher_model.predict(final_features)

        # Trích xuất nhãn dự đoán ý định mua hàng (1: Tự chốt đơn mua, 0: Bỏ đi không mua)
        is_going_to_buy = int(prediction[0])

        # LOGIC CHIẾN LƯỢC: Khách có xu hướng không mua (0) + Lướt xem sản phẩm kỹ (>= 120 giây)
        if is_going_to_buy == 0 and params.productrelated_duration >= 120:
            need_voucher = 1
            discount_percent = 15
            print(f"[AI Quyết Định] Phát hiện khách phân vân (Revenue=0, Thời gian={params.productrelated_duration}s) -> CẤP VOUCHER GIỮ CHÂN!")
        else:
            need_voucher = 0
            discount_percent = 0
            print(f"[AI Quyết Định] Khách chắc chắn tự mua (Revenue=1) hoặc lướt hời hợt -> TỪ CHỐI CẤP VOUCHER.")

        return {
            "need_voucher": need_voucher,
            "discount_percent": discount_percent,
            "status": "success",
            "debug_info": {
                "predicted_revenue_intent": is_going_to_buy
            }
        }
        
    except Exception as e:
        return {"need_voucher": 0, "discount_percent": 0, "error": f"Lỗi ma trận cây quyết định: {str(e)}"}
if voucher_model is not None and hasattr(voucher_model, "feature_names_in_"):
    print("\n🌲=== TOÀN BỘ CẤU TRÚC LUẬT RẼ NHÁNH CỦA CÂY QUYẾT ĐỊNH ===")
    print(export_text(voucher_model, feature_names=list(voucher_model.feature_names_in_)))
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)
    
