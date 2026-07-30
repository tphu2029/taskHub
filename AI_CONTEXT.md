# Thông tin dự án TaskHub_ (Dành cho AI Assistant)

**Tên dự án:** TaskHub_
**Loại dự án:** Backend API
**Framework:** FastAPI (Python)
**Database:** PostgreSQL (SQLAlchemy AsyncSession)
**Caching:** Redis

---

## 1. Cấu trúc thư mục (Architecture)
Dự án được tổ chức theo mô hình Layered Architecture:
*   `app/api/v1/endpoints/`: Chứa các file Router (Controller). Chịu trách nhiệm định tuyến, nhận HTTP Request, gọi Service và trả về Response.
*   `app/services/`: Chứa nghiệp vụ lõi (Business Logic). Mọi thao tác CRUD, kiểm tra quyền (Authorization), xử lý dữ liệu phức tạp, tương tác với Redis Cache đều nằm ở đây.
*   `app/models/`: Định nghĩa các cấu trúc bảng (Table) trong PostgreSQL bằng SQLAlchemy ORM.
*   `app/schemas/`: Định nghĩa các Pydantic models dùng để Validate đầu vào (Request Body) và định dạng đầu ra (Response Model).
*   `app/core/`: Chứa các cấu hình cốt lõi (Database session, Redis client, Security/JWT, Settings).

---

## 2. Các thực thể chính (Entities)
Hệ thống xoay quanh 6 thực thể chính, được phân cấp từ trên xuống dưới:
1.  **User**: Người dùng hệ thống (có thông tin xác thực).
2.  **Workspace**: Không gian làm việc chung. Một User có thể thuộc nhiều Workspace với các vai trò khác nhau (`WorkspaceMember`).
3.  **Project**: Dự án, thuộc về một Workspace cụ thể.
4.  **Task**: Công việc, thuộc về một Project cụ thể. Có các thuộc tính như trạng thái (status), độ ưu tiên (priority), người được giao (assignee).
5.  **Label**: Nhãn phân loại công việc thuộc về một Project cụ thể và có liên kết Nhiều - Nhiều với Task (`TaskLabel`).
6.  **Comment**: Bình luận trên công việc, thuộc về một Task và lưu vết người đăng (`author_id`).

---

## 3. Quy trình chuẩn khi thêm tính năng mới (Workflow)
Khi User yêu cầu thêm một tính năng hoặc thực thể mới, AI cần làm theo các bước sau:
1.  **Model**: Tạo/Cập nhật bảng trong `app/models/`.
2.  **Schema**: Định nghĩa Pydantic models trong `app/schemas/` (VD: `Create`, `Update`, `Response`).
3.  **Service**: Viết logic trong `app/services/`. 
    *   *Lưu ý quan trọng:* Các thao tác liên quan đến Project/Task/Label/Comment **bắt buộc** phải có hàm kiểm tra quyền truy cập thông qua Workspace (VD: `_check_workspace_membership...`).
    *   *Lưu ý về Cache:* Nếu thay đổi dữ liệu (Create/Update/Delete/Assign Label), phải gọi hàm `invalidate_..._cache` trên Redis.
4.  **Endpoint**: Thêm Router trong `app/api/v1/endpoints/` và gọi Service tương ứng.
    *   *Quy tắc thiết kế RESTful:* Sử dụng URL lồng nhau (Nested URL) cho Create/List (VD: `/projects/{id}/tasks`, `/tasks/{id}/comments`), và URL đơn cho Update/Delete (VD: `/tasks/{id}`, `/comments/{id}`).
5.  **Tích hợp (Nếu tạo Router mới)**: Nhớ đăng ký router vào `app/main.py` hoặc `app/api/v1/router.py`.

---

## 4. Tình trạng hiện tại
*   Đã hoàn thiện các chức năng Authentication (Đăng nhập, đăng ký, tạo Token, Refresh & Logout).
*   Đã có đầy đủ CRUD cơ bản và phân quyền cho User, Workspace, Project, Task, Label, Comment.
*   Đã hỗ trợ gán/bỏ Label cho Task và tự động quản lý cache Redis.
*   Đã tích hợp Redis để lưu trữ Cache khi `GET` danh sách Project/Task.

*(File này đóng vai trò là "Bộ nhớ dài hạn" của AI. Bất cứ khi nào bắt đầu một phiên làm việc mới, AI hãy đọc file này để lấy lại toàn bộ bối cảnh dự án trước khi lập trình.)*
