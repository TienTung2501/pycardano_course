"""
Startup script for the Backend API
Run this from the project root directory.
"""
import os
import sys
# Thêm đường dẫn của thư mục backend vào biến môi trường sys.path
# thư việc thêm đường dẫn này giúp cho việc nhập các module trong dự án trở nên dễ dàng hơn
# Dùng để đảm bảo rằng các mô-đun trong thư mục backend có thể được nhập đúng cách
project_root = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))
import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[project_root]
    )
