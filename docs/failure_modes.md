# Failure Modes và cách khắc phục

Một failure mode chính của hệ thống là API tìm kiếm hoặc LLM bị timeout, rate limit,
trả về dữ liệu rỗng hoặc tạo nội dung thiếu nguồn. Supervisor cũng có thể định tuyến
lặp, làm workflow tiêu tốn token nhưng không tạo được câu trả lời cuối. Hệ thống xử
lý bằng cách giới hạn `max_iterations` và thời gian chạy, retry mỗi worker tối đa hai
lần, kiểm tra output sau từng bước, ghi lỗi vào trace và trả về partial fallback answer
khi agent vẫn thất bại. Đối với nguồn yếu hoặc citation bị thiếu, Researcher lưu URL
và metadata của nguồn, Writer tạo riêng phần `Sources`, còn benchmark đo citation
coverage để phát hiện vấn đề.

## Failure modes cụ thể

| Failure mode | Dấu hiệu | Cách khắc phục |
|---|---|---|
| LLM/search timeout | Request chậm hoặc không phản hồi | Timeout, retry và fallback |
| Rate limit/provider error | HTTP 429 hoặc lỗi API | Retry có backoff, giảm số request |
| Search trả về rỗng | Không có sources/research notes | Validation và partial result |
| Citation yếu hoặc thiếu | Citation coverage thấp | Lưu URL từ Researcher và kiểm tra Sources |
| Routing loop | Route lặp, token tăng | `max_iterations` và stop condition |
| Context loss khi handoff | Writer bỏ sót evidence | Shared state và schema rõ ràng |

## Bằng chứng trong implementation

- `services/llm_client.py`: timeout và retry cho provider request.
- `graph/workflow.py`: worker retry, max iterations, stop condition và fallback.
- `agents/researcher.py`: validation nguồn và research notes.
- `agents/writer.py`: validation final answer và tạo danh sách nguồn.
- `evaluation/benchmark.py`: failure rate và citation coverage.
- `reports/benchmark_traces.json`: route, duration và lỗi của từng bước chạy.
