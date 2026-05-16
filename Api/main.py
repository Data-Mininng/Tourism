from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# Nhập 2 thằng cu ly vào làm việc
import database
import rule_generator

app = FastAPI()

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

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)