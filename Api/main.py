from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware

# Nhập 2 thằng cu ly vào làm việc
import database
import rule_generator

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các nguồn (bao gồm cả https://localhost:7180) gọi tới
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Bắt buộc phải có OPTIONS
    allow_headers=["*"],
)

class RuleParams(BaseModel):
    min_support: float = 0.1
    min_confidence: float = 0.5

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
def get_recommendations(service_name: str, limit: int = 3):
    try:
        if not service_name or service_name.strip() == "":
            return {"status": "success", "data": []}

        # Bốc mớ hành vi vết lướt từ JavaScript gửi sang biến thành set tập hợp
        current_user_behaviors = set([b.strip() for b in service_name.split(",") if b.strip()])

        # Lấy bảng luật lên từ SQL Server
        query = "SELECT DichVu_Goc, DichVu_GoiY, Do_Tin_Cay_Confidence FROM Luat_FPGrowth"
        df_rules = pd.read_sql(query, database.engine)

        valid_rules = []

        for index, row in df_rules.iterrows():
            # Chuyển vế trái của dòng luật hiện tại trong DB thành set
            db_rule_antecedent = set([item.strip() for item in row['DichVu_Goc'].split(",") if item.strip()])

            # Kiểm tra xem tổ hợp lướt web hiện tại của khách có chứa trọn vế gốc của luật này không
            if db_rule_antecedent.issubset(current_user_behaviors):
                
                # Loại bỏ không gợi ý lại những gì khách ĐÃ lướt qua hoặc đang xem
                v_phai_items = [i.strip() for i in row['DichVu_GoiY'].split(",") if i.strip()]
                if not any(item in current_user_behaviors for item in v_phai_items):
                    valid_rules.append({
                        "DichVu_Goc": row['DichVu_Goc'],
                        "DichVu_GoiY": row['DichVu_GoiY'],
                        "Do_Tin_Cay_Confidence": float(row['Do_Tin_Cay_Confidence'])
                    })

        if len(valid_rules) > 0:
            df_result = pd.DataFrame(valid_rules)
            df_result = df_result.sort_values(by="Do_Tin_Cay_Confidence", ascending=False)
            df_result = df_result.groupby("DichVu_GoiY").first().reset_index()
            df_result = df_result.sort_values(by="Do_Tin_Cay_Confidence", ascending=False).head(limit)
            
            return {"status": "success", "data": df_result.to_dict(orient="records")}
        
        return {"status": "success", "data": []}

    except Exception as e:
        return {"status": "error", "message": str(e)}
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)