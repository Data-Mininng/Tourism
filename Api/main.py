import os
import joblib
import numpy as np
import pandas as pd
import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.tree import export_text

# Import các module nội bộ hệ thống
import database
import rule_generator

app = FastAPI(
    title="Rule and Decision Tree API",
    description="Backend service hỗ trợ khai phá luật kết hợp FP-Growth và cây quyết định dự đoán Voucher.",
    version="1.0.0"
)

# Cấu hình CORS an toàn cho phép kết nối từ phía client ứng dụng
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# =====================================================================
# 1. ĐỊNH NGHĨA SCHEMAS (DATA MODELS)
# =====================================================================

class RuleParams(BaseModel):
    min_support: float = 0.05
    min_confidence: float = 0.3

class VoucherPredictParams(BaseModel):
    administrative_duration: float
    informational_duration: float
    productrelated_duration: float
    bounce_rates: float
    exit_rates: float
    page_values: float
    weekend: int

# =====================================================================
# 2. KHỞI TẠO VÀ TẢI MÔ HÌNH (MODEL LOADER)
# =====================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOUCHER_DIR = os.path.join(BASE_DIR, "..", "Dataset", "Voucher")

voucher_model = None
voucher_scaler = None

try:
    model_path = os.path.join(VOUCHER_DIR, "mo_hinh_quyet_dinh_voucher.pkl")
    scaler_path = os.path.join(VOUCHER_DIR, "scaler_voucher.pkl")
    
    if not os.path.exists(scaler_path):
        scaler_path = os.path.join(VOUCHER_DIR, "bo_chuan_hoa_voucher.pkl")
        
    voucher_model = joblib.load(model_path)
    voucher_scaler = joblib.load(scaler_path)
    print("✅ Load model và scaler thành công!")
    
    if hasattr(voucher_model, "feature_names_in_"):
        print(f"   Model features: {list(voucher_model.feature_names_in_)}")
    if hasattr(voucher_scaler, "feature_names_in_"):
        print(f"   Scaler features: {list(voucher_scaler.feature_names_in_)}")
except Exception as e:
    print(f"⚠️ Không thể load mô hình học máy: {e}")

# =====================================================================
# 3. ENDPOINT: HUẤN LUYỆN LUẬT KẾT HỢP (FP-GROWTH)
# =====================================================================

@app.post("/api/train-rules")
def train_rules_endpoint(params: RuleParams):
    try:
        csv_path = os.path.abspath(os.path.join(BASE_DIR, "..", "Dataset", "tourism_dataset_5k.csv"))
        if not os.path.exists(csv_path):
            return {"status": "error", "message": f"Không tìm thấy file data gốc tại: {csv_path}"}
                    
        df_transactions = pd.read_csv(csv_path)
        df_rules = rule_generator.run_fpgrowth(df_transactions, params.min_support, params.min_confidence)
                
        if not df_rules.empty:
            df_rules.columns = ['DichVu_Goc', 'DichVu_GoiY', 'Do_Ho_Tro', 'Do_Tin_Cay_Confidence', 'Chi_So_Lift']
            
        database.save_rules(df_rules)
        return {
            "status": "success",
            "message": "Cập nhật luật thành công!",
            "total_rules_generated": len(df_rules)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# =====================================================================
# 4. ENDPOINT: GỢI Ý DỊCH VỤ CƠ BẢN (LEGACY RECOMMENDATIONS)
# =====================================================================

@app.get("/api/recommendations")
def get_recommendations(service_name: str = Query(None), limit: int = 4):
    try:
        if not service_name or not service_name.strip():
            return {"status": "success", "data": []}
            
        current_items = {b.strip() for b in service_name.split(",") if b.strip()}
        
        # Đọc dữ liệu bảng luật từ DB (Tương thích cả 2 cách đặt tên bảng)
        try:
            query = "SELECT DichVu_Goc, DichVu_GoiY, Do_Tin_Cay_Confidence, Chi_So_Lift FROM Luat_FPGrowth"
            df_rules = pd.read_sql(query, database.engine)
        except Exception:
            try:
                query = "SELECT DichVu_Goc, DichVu_GoiY, Do_Tin_Cay_Confidence, Chi_So_Lift FROM LuatFPGrowth"
                df_rules = pd.read_sql(query, database.engine)
            except Exception as e2:
                return {"status": "error", "message": f"Không đọc được bảng luật từ database: {str(e2)}"}
                
        if df_rules.empty:
            return {"status": "success", "data": []}
            
        valid_rules = []
        for _, row in df_rules.iterrows():
            antecedent = {i.strip() for i in str(row["DichVu_Goc"]).split(",") if i.strip()}
            if not antecedent or not antecedent.issubset(current_items):
                continue
                
            consequents = [i.strip() for i in str(row["DichVu_GoiY"]).split(",") if i.strip()]
            if any(c in current_items for c in consequents):
                continue
                
            valid_rules.append({
                "DichVu_Goc": str(row["DichVu_Goc"]).strip(),
                "DichVu_GoiY": str(row["DichVu_GoiY"]).strip(),
                "Do_Tin_Cay_Confidence": float(row["Do_Tin_Cay_Confidence"]),
                "Chi_So_Lift": float(row.get("Chi_So_Lift", 1.0)),
            })
            
        if not valid_rules:
            return {"status": "success", "data": []}
            
        df_result = pd.DataFrame(valid_rules)
        df_result = df_result.sort_values("Do_Tin_Cay_Confidence", ascending=False)
        df_result = df_result.groupby("DichVu_GoiY").first().reset_index()
        df_result = df_result.sort_values("Do_Tin_Cay_Confidence", ascending=False).head(limit)
        
        return {"status": "success", "data": df_result.to_dict(orient="records")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# =====================================================================
# 5. ENDPOINT: GỢI Ý DỊCH VỤ ĐA NGỮ CẢNH (ADVANCED RECOMMENDATIONS)
# =====================================================================

def _extract_context_from_items(items: set) -> dict:
    """Tách lọc và ánh xạ tiền tố chuỗi thành cấu trúc ngữ cảnh tường minh."""
    ctx = {}
    
    # Định nghĩa ánh xạ từ Prefix sang Key trong Dictionary kết quả
    prefix_map = {
        "Den_": "destinations",
        "TuDen_": "origins",
        "Hang_": "airlines",
        "KhachSan_": "hotel_types",
        "NganSach_": "budgets",
        "Mua_": "seasons",
        "SoNgay_": "durations",
        "Xe_": "car_brands",
        "SoNguoi_": "group_sizes",
        "MucDich_": "purposes",
        "HD_": "activities"
    }
    
    for item in items:
        for prefix, key in prefix_map.items():
            if item.startswith(prefix):
                val = item.replace(prefix, "")
                ctx.setdefault(key, []).append(val)
                break
                
    # Logic kiểm tra trạng thái hồ bơi đặc thù
    if "Co_Ho_Boi" in items:
        ctx["has_pool"] = True
    elif "Khong_Ho_Boi" in items:
        ctx["has_pool"] = False
        
    return ctx

@app.get("/api/recommendations-with-context")
def get_recommendations_with_context(service_name: str = Query(None), limit: int = 5):
    try:
        if not service_name or not service_name.strip():
            return {"status": "success", "data": []}
            
        current_items = {b.strip() for b in service_name.split(",") if b.strip()}
        extracted_ctx = _extract_context_from_items(current_items)
        
        try:
            query = "SELECT DichVu_Goc, DichVu_GoiY, Do_Tin_Cay_Confidence, Chi_So_Lift FROM Luat_FPGrowth"
            df_rules = pd.read_sql(query, database.engine)
        except Exception:
            try:
                query = "SELECT DichVu_Goc, DichVu_GoiY, Do_Tin_Cay_Confidence, Chi_So_Lift FROM LuatFPGrowth"
                df_rules = pd.read_sql(query, database.engine)
            except Exception as e2:
                return {"status": "error", "message": f"Không đọc được bảng luật: {str(e2)}"}
                
        if df_rules.empty:
            return {"status": "success", "data": [], "extracted_context": extracted_ctx}
            
        valid_rules = []
        SERVICE_PREFIX = ("DV_", "HD_")
        
        # Vòng lặp 1: Tìm kiếm khớp hoàn toàn (Exact Subset Match)
        for _, row in df_rules.iterrows():
            antecedent = {i.strip() for i in str(row["DichVu_Goc"]).split(",") if i.strip()}
            if not antecedent or not antecedent.issubset(current_items):
                continue
                
            consequents = [i.strip() for i in str(row["DichVu_GoiY"]).split(",") if i.strip()]
            service_consequents = [c for c in consequents if c.startswith(SERVICE_PREFIX)]
            
            if not service_consequents or any(c in current_items for c in service_consequents):
                continue
                
            valid_rules.append({
                "DichVu_Goc": str(row["DichVu_Goc"]).strip(),
                "DichVu_GoiY": ",".join(service_consequents),
                "Do_Tin_Cay_Confidence": float(row["Do_Tin_Cay_Confidence"]),
                "Chi_So_Lift": float(row.get("Chi_So_Lift", 1.0)),
                "extracted_context": extracted_ctx,
            })
            
        # Vòng lặp 2: Tìm kiếm khớp một phần nếu tập khớp hoàn toàn trống (Partial Match >= 50%)
        if not valid_rules:
            for _, row in df_rules.iterrows():
                antecedent = {i.strip() for i in str(row["DichVu_Goc"]).split(",") if i.strip()}
                if not antecedent:
                    continue
                    
                overlap = len(antecedent & current_items) / len(antecedent)
                if overlap < 0.5:
                    continue
                    
                consequents = [i.strip() for i in str(row["DichVu_GoiY"]).split(",") if i.strip()]
                service_consequents = [c for c in consequents if c.startswith(SERVICE_PREFIX)]
                
                if not service_consequents or any(c in current_items for c in service_consequents):
                    continue
                    
                valid_rules.append({
                    "DichVu_Goc": str(row["DichVu_Goc"]).strip(),
                    "DichVu_GoiY": ",".join(service_consequents),
                    "Do_Tin_Cay_Confidence": float(row["Do_Tin_Cay_Confidence"]) * overlap,
                    "Chi_So_Lift": float(row.get("Chi_So_Lift", 1.0)),
                    "extracted_context": extracted_ctx,
                    "partial_match": True,
                })
                
        if not valid_rules:
            return {"status": "success", "data": [], "extracted_context": extracted_ctx}
            
        df_result = pd.DataFrame(valid_rules)
        df_result = df_result.sort_values("Do_Tin_Cay_Confidence", ascending=False)
        df_result = df_result.groupby("DichVu_GoiY").first().reset_index()
        df_result = df_result.sort_values("Do_Tin_Cay_Confidence", ascending=False).head(limit)
        
        result_list = df_result.to_dict(orient="records")
        for r in result_list:
            if "extracted_context" not in r or not r["extracted_context"]:
                r["extracted_context"] = extracted_ctx
                
        return {
            "status": "success",
            "data": result_list,
            "extracted_context": extracted_ctx
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# =====================================================================
# 6. ENDPOINT: DỰ ĐOÁN PHÁT VOUCHER (DECISION TREE INFERENCE)
# =====================================================================

@app.post("/api/predict-voucher")
def predict_voucher_endpoint(params: VoucherPredictParams):
    try:
        if voucher_model is None or voucher_scaler is None:
            return {
                "need_voucher": 0,
                "discount_percent": 0,
                "error": "Model chưa được load. Kiểm tra thư mục Dataset/Voucher/"
            }
            
        param_map = {
            "administrative_duration": params.administrative_duration,
            "informational_duration": params.informational_duration,
            "productrelated_duration": params.productrelated_duration,
            "bounce_rates": params.bounce_rates,
            "exit_rates": params.exit_rates,
            "page_values": params.page_values,
            "weekend": 1 if params.weekend else 0,
        }
        
        clean_map = {k.lower().replace("_", ""): v for k, v in param_map.items()}
        
        # Thực hiện chuẩn hóa dữ liệu đầu vào (Scaling)
        if hasattr(voucher_scaler, "feature_names_in_"):
            scaler_cols = list(voucher_scaler.feature_names_in_)
            scaler_data = {col: clean_map.get(col.lower().replace("_", ""), 0.0) for col in scaler_cols}
            scaled = voucher_scaler.transform(pd.DataFrame([scaler_data]))
        else:
            numeric = np.array([[
                params.administrative_duration, params.informational_duration,
                params.productrelated_duration, params.bounce_rates,
                params.exit_rates, params.page_values
            ]])
            scaled = voucher_scaler.transform(numeric)
            
        # Đưa dữ liệu qua mô hình học máy để dự đoán hành vi mua hàng
        if hasattr(voucher_model, "feature_names_in_"):
            model_cols = list(voucher_model.feature_names_in_)
            scaler_cols = list(voucher_scaler.feature_names_in_) if hasattr(voucher_scaler, "feature_names_in_") else []
            model_data = {}
            for col in model_cols:
                clean_col = col.lower().replace("_", "")
                if col in scaler_cols:
                    idx = scaler_cols.index(col)
                    model_data[col] = float(scaled[0][idx])
                else:
                    model_data[col] = clean_map.get(clean_col, 0)
            prediction = voucher_model.predict(pd.DataFrame([model_data]))
        else:
            weekend_val = 1 if params.weekend else 0
            final_feats = np.hstack((scaled, [[weekend_val]]))
            prediction = voucher_model.predict(final_feats)
            
        predicted_revenue = int(prediction[0])
        need_voucher = 0
        discount_percent = 0
        decision_reason = ""
        
        # Thực thi cây quyết định logic nghiệp vụ phân phối Voucher
        if predicted_revenue == 0:
            if params.productrelated_duration >= 120 or params.page_values >= 30:
                need_voucher = 1
                if params.page_values >= 60:
                    discount_percent = 20
                    decision_reason = "Revenue=0, page_values cao (≥60) → CẤP 20%"
                elif params.page_values >= 30 or params.productrelated_duration >= 300:
                    discount_percent = 15
                    decision_reason = "Revenue=0, page_values trung bình hoặc xem lâu → CẤP 15%"
                else:
                    discount_percent = 10
                    decision_reason = "Revenue=0, xem sản phẩm ≥120s → CẤP 10%"
            else:
                decision_reason = "Revenue=0 nhưng xem quá ngắn → KHÔNG cấp"
        else:
            decision_reason = "Revenue=1 → khách sẽ tự mua, KHÔNG cấp voucher"
            
        return {
            "need_voucher": need_voucher,
            "discount_percent": discount_percent,
            "status": "success",
            "debug_info": {
                "predicted_revenue_intent": predicted_revenue,
                "decision_reason": decision_reason,
                "product_duration_s": params.productrelated_duration,
                "page_values": params.page_values,
            }
        }
    except Exception as e:
        return {
            "need_voucher": 0,
            "discount_percent": 0,
            "error": f"Lỗi dự đoán: {str(e)}"
        }

# In log cấu trúc cây quyết định lên console khi khởi chạy ứng dụng nhằm kiểm tra tính đúng đắn
if voucher_model is not None and hasattr(voucher_model, "feature_names_in_"):
    print("\n🌲=== CẤU TRÚC CÂY QUYẾT ĐỊNH VOUCHER ===")
    print(export_text(voucher_model, feature_names=list(voucher_model.feature_names_in_), max_depth=4))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)