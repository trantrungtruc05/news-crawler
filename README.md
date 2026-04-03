# News Crawler — TechCrunch AI → Vietnamese

Crawl bài viết từ TechCrunch AI, dịch sang tiếng Việt qua OpenAI, lưu vào PostgreSQL. Job tự động chạy mỗi 12 tiếng.

## Yêu cầu

- Python >= 3.11
- PostgreSQL đang chạy
- OpenAI API key

## Cài đặt

```bash
# Clone & vào thư mục project
cd cursor_test

# Tạo virtual environment
python -m venv .venv
source .venv/bin/activate   # macOS/Linux

# Cài dependencies
pip install -e .

# Cài dev tools (tuỳ chọn)
pip install -e ".[dev]"
```

## Cấu hình

```bash
# Copy file mẫu và chỉnh sửa
cp .env.example .env
```

Mở `.env` và cập nhật:
- `DATABASE_URL` — connection string PostgreSQL
- `OPENAI_API_KEY` — API key của bạn

## Tạo database

```bash
createdb news_crawler
```

Bảng `articles` sẽ được tự động tạo khi chạy lần đầu.

## Chạy

```bash
# Chạy pipeline + scheduler
news-crawler

# Hoặc
python -m news_crawler.main
```

Pipeline sẽ:
1. Crawl danh sách bài từ TechCrunch AI (mặc định 3 trang)
2. Scrape nội dung từng bài
3. Dịch sang tiếng Việt qua OpenAI
4. Upsert vào PostgreSQL (bài đã có → update, bài mới → insert)
5. Lặp lại sau mỗi 12 tiếng

## Cấu trúc project

```
src/news_crawler/
├── core/
│   ├── config.py          # Settings từ .env
│   ├── database.py        # SQLAlchemy engine & session
│   └── exceptions.py      # Custom exceptions
├── models/
│   └── article.py         # ORM model & Pydantic schemas
├── services/
│   ├── crawler.py         # Crawl & parse TechCrunch
│   ├── translator.py      # Dịch qua OpenAI API
│   └── repository.py      # Upsert vào DB
└── main.py                # Entry point & scheduler
```

## Schema bảng `articles`

| Column             | Type                     | Ghi chú                  |
|--------------------|--------------------------|--------------------------|
| `url`              | VARCHAR(2048) PK         | URL gốc, dùng làm key   |
| `title_original`   | VARCHAR(1024)            | Tiêu đề tiếng Anh       |
| `title_vi`         | VARCHAR(1024)            | Tiêu đề tiếng Việt      |
| `author`           | VARCHAR(256)             | Tên tác giả              |
| `published_at`     | TIMESTAMP WITH TZ        | Ngày đăng bài            |
| `summary_original` | TEXT                     | Tóm tắt tiếng Anh       |
| `summary_vi`       | TEXT                     | Tóm tắt tiếng Việt      |
| `content_original` | TEXT                     | Nội dung tiếng Anh       |
| `content_vi`       | TEXT                     | Nội dung tiếng Việt      |
| `image_url`        | VARCHAR(2048)            | Ảnh đại diện             |
| `tags`             | VARCHAR(1024)            | Tags, phân cách bằng dấu phẩy |
| `crawled_at`       | TIMESTAMP WITH TZ        | Thời điểm crawl lần đầu |
| `updated_at`       | TIMESTAMP WITH TZ        | Lần cập nhật cuối        |
