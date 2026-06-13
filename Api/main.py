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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# =====================================================================
# PYDANTIC SCHEMAS
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
    weekend: int


# =====================================================================
# KHỞI TẠO MÔ HÌNH VÀ CƠ SỞ DỮ LIỆU KHI START SERVER
# =====================================================================

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
VOUCHER_DIR = os.path.join(BASE_DIR, "..", "Dataset", "Voucher")

voucher_model  = None
voucher_scaler = None

try:
    model_path  = os.path.join(VOUCHER_DIR, "mo_hinh_quyet_dinh_voucher.pkl")
    scaler_path = os.path.join(VOUCHER_DIR, "scaler_voucher.pkl")
    if not os.path.exists(scaler_path):
        scaler_path = os.path.join(VOUCHER_DIR, "bo_chuan_hoa_voucher.pkl")
        
    voucher_model  = joblib.load(model_path)
    voucher_scaler = joblib.load(scaler_path)
    print("✅ [AI] Đã nạp mô hình Cây quyết định và Bộ chuẩn hóa thành công!")
except Exception as e:
    print(f"⚠️ [AI] Cảnh báo lỗi nạp mô hình: {e}")

try:
    database.init_log_tables()
except Exception as e:
    print(f"⚠️ [DB] Cảnh báo không thể khởi tạo cấu trúc bảng log: {e}")


# =====================================================================
# ENDPOINT: HUẤN LUYỆN LUẬT (Đã đồng bộ với DB, bỏ CSV)
# =====================================================================

@app.post("/api/train-rules")
def train_rules_endpoint(params: RuleParams):
    try:
        # Lấy dữ liệu trực tiếp từ SQL Server thay vì đọc file CSV tĩnh
        df_transactions = database.get_transactions()
        
        # Chạy thuật toán FP-Growth sinh luật
        df_rules = rule_generator.run_fpgrowth(df_transactions, params.min_support, params.min_confidence)
        
        # Lưu vào bảng Luat_FPGrowth
        database.save_rules(df_rules)
        return {
            "status": "success",
            "message": "Đã lấy dữ liệu DB thực tế và cập nhật tập luật thành công!",
            "total_rules_generated": len(df_rules)
        }
    except Exception as e:
        return {"status": "error", "message": f"Thất bại khi huấn luyện: {str(e)}"}


# =====================================================================
# ENDPOINT: GỢI Ý DỊCH VỤ (Đã chuẩn hóa tên bảng Luat_FPGrowth)
# =====================================================================

@app.get("/api/recommendations")
def get_recommendations(service_name: str = Query(None), limit: int = 3):
    try:
        if not service_name or service_name.strip() == "":
            return {"status": "success", "data": []}

        current_user_behaviors = set([b.strip() for b in service_name.split(",") if b.strip()])

        # Đồng bộ gọi duy nhất bảng Luat_FPGrowth đã chốt thiết kế
        query = "SELECT DichVu_Goc, DichVu_GoiY, Do_Tin_Cay_Confidence FROM Luat_FPGrowth"
        df_rules = pd.read_sql(query, database.engine)

        if df_rules.empty:
            return {"status": "success", "data": []}

        valid_rules = []
        for _, row in df_rules.iterrows():
            db_rule_antecedent = set([item.strip() for item in str(row['DichVu_Goc']).split(",") if item.strip()])
            
            # Kiểm tra hành vi hiện tại có chứa vế trái của luật không
            if db_rule_antecedent and db_rule_antecedent.issubset(current_user_behaviors):
                v_phai_items = [i.strip() for i in str(row['DichVu_GoiY']).split(",") if i.strip()]
                
                # Tránh gợi ý trùng với những dịch vụ người dùng đã có
                if not any(item in current_user_behaviors for item in v_phai_items):
                    valid_rules.append({
                        "DichVu_Goc": str(row['DichVu_Goc']).strip(),
                        "DichVu_GoiY": str(row['DichVu_GoiY']).strip(),
                        "Do_Tin_Cay_Confidence": float(row['Do_Tin_Cay_Confidence'])
                    })

        if valid_rules:
            df_result = pd.DataFrame(valid_rules)
            df_result = df_result.sort_values(by="Do_Tin_Cay_Confidence", ascending=False)
            df_result = df_result.groupby("DichVu_GoiY").first().reset_index()
            df_result = df_result.sort_values(by="Do_Tin_Cay_Confidence", ascending=False).head(limit)
            return {"status": "success", "data": df_result.to_dict(orient="records")}

        return {"status": "success", "data": []}

    except Exception as e:
        return {"status": "error", "message": f"Lỗi gợi ý: {str(e)}"}


# =====================================================================
# ENDPOINT: DỰ ĐOÁN VOUCHER CÂY QUYẾT ĐỊNH
# =====================================================================

@app.post("/api/predict-voucher")
def predict_voucher_endpoint(params: VoucherPredictParams):
    input_log_id = None
    try:
        input_log_id = database.save_voucher_input_log(params.dict())
    except Exception as db_err:
        print(f"[LOG ERROR] Lỗi ghi VoucherInputLog: {db_err}")

    if voucher_model is None or voucher_scaler is None:
        reason = "Mô hình chưa được nạp lên máy chủ Python."
        if input_log_id:
            try: database.save_voucher_predict_log(input_log_id, -1, 0, 0, reason)
            except Exception as d_e: print(f"[LOG ERROR] {d_e}")
        return {"need_voucher": 0, "discount_percent": 0, "error": reason}

    try:
        param_mapping = {
            "administrative_duration": params.administrative_duration,
            "informational_duration" : params.informational_duration,
            "productrelated_duration": params.productrelated_duration,
            "bounce_rates"           : params.bounce_rates,
            "exit_rates"             : params.exit_rates,
            "page_values"            : params.page_values,
            "weekend"                : 1 if params.weekend else 0,
        }
        clean_param_map = {k.lower().replace("_", ""): v for k, v in param_mapping.items()}

        # Chuẩn hóa dữ liệu bằng Scaler
        if hasattr(voucher_scaler, "feature_names_in_"):
            scaler_features = list(voucher_scaler.feature_names_in_)
            aligned_scaler_data = {
                col: clean_param_map.get(col.lower().replace("_", ""), 0.0) for col in scaler_features
            }
            input_df = pd.DataFrame([aligned_scaler_data])
            numeric_scaled = voucher_scaler.transform(input_df)
        else:
            numeric_features = np.array([[
                params.administrative_duration, params.informational_duration,
                params.productrelated_duration, params.bounce_rates,
                params.exit_rates, params.page_values
            ]])
            numeric_scaled = voucher_scaler.transform(numeric_features)

        # Dự đoán bằng Cây Quyết Định (Decision Tree)
        if hasattr(voucher_model, "feature_names_in_"):
            model_features = list(voucher_model.feature_names_in_)
            scaler_cols = list(voucher_scaler.feature_names_in_) if hasattr(voucher_scaler, "feature_names_in_") else []
            aligned_model_data = {}
            for col in model_features:
                clean_col = col.lower().replace("_", "")
                if col in scaler_cols:
                    idx = scaler_cols.index(col)
                    aligned_model_data[col] = numeric_scaled[0][idx]
                else:
                    aligned_model_data[col] = clean_param_map.get(clean_col, 0)
            final_df = pd.DataFrame([aligned_model_data])
            prediction = voucher_model.predict(final_df)
        else:
            weekend_val    = 1 if params.weekend else 0
            final_features = np.hstack((numeric_scaled, [[weekend_val]]))
            prediction     = voucher_model.predict(final_features)

        is_going_to_buy = int(prediction[0])

        # Chiến lược kích cầu: Khách không định mua (Revenue=0) nhưng xem sản phẩm lâu -> Tặng voucher
        if is_going_to_buy == 0 and params.productrelated_duration >= 120:
            need_voucher    = 1
            discount_percent = 15
            reason = f"Revenue=0, ProductDuration={params.productrelated_duration}s >= 120s → CẤP VOUCHER GIỮ CHÂN"
        else:
            need_voucher    = 0
            discount_percent = 0
            reason = f"Revenue={is_going_to_buy}, ProductDuration={params.productrelated_duration}s → KHÔNG CẤP"

        # Ghi Log kết quả dự đoán xuống DB
        if input_log_id:
            try:
                database.save_voucher_predict_log(
                    input_log_id, is_going_to_buy, need_voucher, discount_percent, reason
                )
            except Exception as db_err:
                print(f"[LOG ERROR] Lỗi ghi VoucherPredictLog: {db_err}")

        return {
            "need_voucher"    : need_voucher,
            "discount_percent": discount_percent,
            "status"          : "success",
            "debug_info"      : {
                "predicted_revenue_intent": is_going_to_buy,
                "decision_reason"         : reason,
            }
        }

    except Exception as e:
        reason = f"Lỗi cây quyết định: {str(e)}"
        if input_log_id:
            try: database.save_voucher_predict_log(input_log_id, -1, 0, 0, reason)
            except Exception as db_err: print(f"[LOG ERROR] {db_err}")
        return {"need_voucher": 0, "discount_percent": 0, "error": reason}


if voucher_model is not None and hasattr(voucher_model, "feature_names_in_"):
    print("\n🌲=== CẤU TRÚC CÂY QUYẾT ĐỊNH HIỆN TẠI ===")
    print(export_text(voucher_model, feature_names=list(voucher_model.feature_names_in_)))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)