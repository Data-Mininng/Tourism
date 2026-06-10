import os
import subprocess
import sys

def check_and_install_requirements():
    """Tự động cài thư viện (Chỉ chạy khi thiếu thư viện)"""
    if os.path.exists("requirements.txt"):
        print("🔍 Đang kiểm tra thư viện hệ thống...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True, stdout=subprocess.DEVNULL)
            print("✅ Thư viện đã sẵn sàng!")
        except Exception:
            print("⚠️ Không thể tự cập nhật thư viện, sẽ dùng thư viện hiện tại của máy.")

def run_script(script_path, description):
    """Hàm chạy file con bằng cách chuyển môi trường làm việc vào đúng thư mục của file đó"""
    print(f"\n🚀 BẮT ĐẦU: {description}...")
    
    # Lấy thư mục chứa file cần chạy và tên file
    working_dir = os.path.dirname(script_path)
    script_name = os.path.basename(script_path)
    
    # Chạy script từ chính thư mục gốc của nó để tránh lỗi đường dẫn nội bộ của script đó
    result = subprocess.run([sys.executable, script_name], cwd=working_dir if working_dir else None)
    
    if result.returncode != 0:
        print(f"❌ LỖI: Bước [{description}] thất bại. Dừng hệ thống.")
        sys.exit(1)
    print(f"✅ HOÀN THÀNH: {description}.")

def main():
    print("==========================================================")
    print("🔥 HỆ THỐNG PIPELINE THÔNG MINH - KHAI PHÁ DỮ LIỆU 🔥")
    print("==========================================================")
    
    # 1. Kiểm tra thư viện
    check_and_install_requirements()

    # ------------------ KIỂM TRA VÀ CHẠY LUỒNG TỰ ĐỘNG ------------------
    
    # Bước 1: Tạo dữ liệu giả lập Du lịch (Chỉ chạy nếu CHƯA CÓ file tourism_dataset_5k.csv)
    if not os.path.exists("Dataset/tourism_dataset_5k.csv"):
        if os.path.exists("Dataset/create_tourism_dataset_5k.py"):
            run_script("Dataset/create_tourism_dataset_5k.py", "Tạo dữ liệu giả lập Du lịch 5K dòng")
        else:
            print("⚠️ Không tìm thấy file 'Dataset/create_tourism_dataset_5k.py' để tạo data gốc.")
    else:
        print("⏭️  [Bỏ qua]: Đã có file 'tourism_dataset_5k.csv', không cần tạo lại.")

    # Bước 2: Tiền xử lý dữ liệu du lịch
    if not os.path.exists("Dataset/tourism_dataset_preprocessed.csv"):
        if os.path.exists("Dataset/preprocess.py"):
            run_script("Dataset/preprocess.py", "Tiền xử lý dữ liệu Du lịch")
    else:
        print("⏭️  [Bỏ qua]: Đã có dữ liệu tiền xử lý Du lịch.")

    # Bước 3: Tiền xử lý dữ liệu online_shoppers_intention
    if not os.path.exists("Dataset/du_lieu_da_xu_ly.csv"):
        if os.path.exists("Dataset/Voucher/2_tien_xu_ly.py"):
            run_script("Dataset/Voucher/2_tien_xu_ly.py", "Tiền xử lý dữ liệu Online Shoppers")
    else:
        print("⏭️  [Bỏ qua]: Đã có file 'du_lieu_da_xu_ly.csv'.")

    # Bước 4 & 5: Train và Đóng gói Model AI (Đã sửa đường dẫn kiểm tra chuẩn về thư mục Voucher)
    if not os.path.exists("Dataset/Voucher/mo_hinh_quyet_dinh_voucher.pkl"):
        print("\n🤖 Phát hiện thiếu file Model AI. Tiến hành huấn luyện tự động...")
        
        if os.path.exists("Dataset/Voucher/4_dong_goi_mo_hinh.py"):
            run_script("Dataset/Voucher/4_dong_goi_mo_hinh.py", "Huấn luyện chung cuộc và đóng gói mô hình (.pkl)")
        else:
            print("⚠️ Không tìm thấy file 'Dataset/Voucher/4_dong_goi_mo_hinh.py' để đóng gói.")
    else:
        print("⏭️  [Bỏ qua]: Đã có file mô hình AI 'mo_hinh_quyet_dinh_voucher.pkl', sẵn sàng dự đoán.")

    # ------------------ KHỞI ĐỘNG SERVER ------------------
    print("\n=========================================")
    print("🌐 KHỞI ĐỘNG SERVER API (FASTAPI)...")
    print("=========================================\n")
    
    try:
        # Gọi file main.py chứa FastAPI để bật cổng lắng nghe ứng dụng .NET
        if os.path.exists("Api/main.py"):
            subprocess.run([sys.executable, "main.py"], cwd="Api")
        else:
            print("❌ LỖI: Không tìm thấy file 'Api/main.py' để khởi động Server API.")
    except KeyboardInterrupt:
        print("\n👋 Đã tắt Server API.")

if __name__ == "__main__":
    main()