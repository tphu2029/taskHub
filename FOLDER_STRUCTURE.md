# Cấu trúc thư mục dự án TaskHub_

Dưới đây là sơ đồ cấu trúc thư mục của dự án **TaskHub_** cùng với ý nghĩa chi tiết của từng thư mục và file.

## Sơ đồ thư mục

```text
TaskHub_/
├── .git/                   # (Thư mục ẩn) Chứa dữ liệu của Git để quản lý phiên bản mã nguồn.
├── app/                    # Thư mục chứa toàn bộ mã nguồn chính của ứng dụng FastAPI.
│   ├── api/                # Chứa các định nghĩa về API (Routes / Controllers).
│   │   └── v1/             # Đánh dấu phiên bản API (Version 1).
│   │       ├── endpoints/  # Nơi xử lý request/response cho từng thực thể (ví dụ: auth.py, users.py).
│   │       └── router.py   # Tập hợp và đăng ký tất cả các endpoints lại với nhau.
│   ├── core/               # Chứa các thiết lập và cấu hình cốt lõi (config, kết nối database, security, redis, dependencies).
│   ├── models/             # Chứa các ORM Models (VD: SQLAlchemy) định nghĩa cấu trúc bảng trong Database (user.py).
│   ├── schemas/            # Chứa các Pydantic Models dùng để kiểm tra (validate) dữ liệu đầu vào (request) và đầu ra (response).
│   ├── services/           # Tầng Business Logic: Chứa các hàm xử lý nghiệp vụ phức tạp (auth_service, user_service) mà API sẽ gọi.
│   └── main.py             # File khởi tạo ứng dụng FastAPI và nhúng các routers, middlewares...
├── taskhub.egg-info/       # Thư mục tự động sinh ra chứa metadata của thư viện khi project được đóng gói/cài đặt dưới dạng một package Python.
├── .env                    # Chứa các biến môi trường cấu hình bảo mật (Database URL, Secret Keys...).
├── .gitignore              # Chỉ định những file/thư mục không được đẩy (push) lên Git (ví dụ: .env, __pycache__).
├── Dockerfile              # Chứa các chỉ dẫn để build Docker Image cho ứng dụng.
├── docker-compose.yml      # Cấu hình để chạy cùng lúc nhiều containers (Ví dụ: chạy app kết nối với PostgreSQL và Redis cục bộ).
├── main.py                 # File entry point ở thư mục gốc, thường dùng làm điểm chạy server (chạy uvicorn).
├── pyproject.toml          # File cấu hình dự án hiện đại và danh sách các thư viện phụ thuộc (dependencies).
└── README.md               # Tài liệu hướng dẫn cài đặt và sử dụng dự án.
```

## Luồng hoạt động (Kiến trúc phân tầng)

Cấu trúc trong thư mục `app/` được tổ chức theo mô hình **Phân tầng (Layered Architecture)** trong FastAPI, hoạt động theo luồng sau:
1. **Người dùng gửi Request** -> Đi vào thư mục `api/v1/endpoints` (Đóng vai trò là Controller).
2. **Controller** dùng các model trong `schemas/` để kiểm tra tính hợp lệ của dữ liệu đầu vào (Validation).
3. **Controller** gọi các hàm trong `services/` (Business Logic) để xử lý công việc và nghiệp vụ chính.
4. **Service** sẽ sử dụng các cấu trúc định nghĩa ở `models/` và tương tác với Database (thông qua những cấu hình và connection ở `core/`).
5. **Service** trả kết quả lại cho Controller, sau đó Controller trả lại Response cho người dùng theo đúng định dạng được định nghĩa ở `schemas/`.
