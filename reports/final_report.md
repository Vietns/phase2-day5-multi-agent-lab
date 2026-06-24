# Final Report: Multi-Agent Research System

## 1. Tổng quan

Project xây dựng một research assistant có khả năng nhận câu hỏi, thu thập nguồn, phân
tích bằng chứng và tạo câu trả lời cuối có citations. Hệ thống cung cấp hai kiến trúc
để so sánh: single-agent baseline và multi-agent workflow. Multi-agent gồm Supervisor,
Researcher, Analyst và Writer, sử dụng shared state để handoff dữ liệu giữa các bước.

Implementation hỗ trợ Groq và OpenAI thông qua provider abstraction. Khi không có API
key, hệ thống chuyển sang deterministic offline mock để vẫn có thể chạy test. Search
có thể dùng Tavily hoặc local mock corpus. Workflow sử dụng LangGraph khi dependency
được cài và có local fallback cho môi trường tối giản.

## 2. Kiến trúc hệ thống

```text
User Query
    |
    v
Supervisor / Router
    |
    +--> Researcher --> sources + research_notes
    |
    +--> Analyst ----> analysis_notes
    |
    +--> Writer -----> final_answer + citations
    |
    v
Trace + Benchmark Report
```

Supervisor kiểm tra shared state và chọn stage còn thiếu. Researcher tìm và chuẩn hóa
nguồn. Analyst tổng hợp luận điểm, so sánh quan điểm và đánh dấu bằng chứng yếu. Writer
biến analysis thành câu trả lời phù hợp với audience và tạo phần Sources. Optional
Critic kiểm tra contract tối thiểu của final answer.

## 3. Shared state và handoff

`ResearchState` là single source of truth trong workflow. State chứa request,
iteration, route history, sources, research notes, analysis notes, final answer,
agent results, trace và errors. Thiết kế này giúp mỗi agent chỉ đọc input cần thiết và
ghi output vào field rõ ràng, đồng thời giữ đủ context để debug.

Route chuẩn của một run thành công là:

```text
researcher -> analyst -> writer -> done
```

Mỗi agent result lưu content và token metadata. Trace lưu route decision, duration và
provider error. Nhờ đó có thể xác định stage nào gây latency hoặc failure.

## 4. Guardrails

Hệ thống triển khai các guardrail sau:

- Pydantic validation cho query, state và benchmark metrics.
- `max_iterations` ngăn Supervisor tạo routing loop vô hạn.
- Timeout giới hạn thời gian request và toàn workflow.
- LLM request retry với exponential backoff.
- Worker retry hai lần tại workflow boundary.
- Validation output sau Researcher, Analyst và Writer.
- Partial fallback answer khi một stage tiếp tục thất bại.
- JSON trace ghi route, duration và error để phục vụ audit.

Các guardrail này không đảm bảo provider luôn thành công, nhưng bảo đảm lỗi được nhìn
thấy, workflow dừng hữu hạn và người dùng nhận được partial result thay vì state rỗng.

## 5. Thiết lập benchmark

Benchmark sử dụng query:

```text
Research GraphRAG state-of-the-art and write a 500-word summary
```

Groq với model `llama-3.3-70b-versatile` được dùng cho LLM calls. Search sử dụng local
mock corpus vì Tavily chưa được cấu hình tại thời điểm chạy. Baseline và multi-agent
dùng cùng query và sources để phép so sánh tập trung vào orchestration.

## 6. Kết quả

| Metric | Single-agent | Multi-agent |
|---|---:|---:|
| Latency | 5.424 giây | 8.927 giây |
| Quality heuristic | 10.0/10 | 10.0/10 |
| Citation coverage | 100% | 100% |
| Failure rate | 0% | 0% |
| Input/output tokens | 187/772 | 1533/1916 |
| Tổng tokens | 959 | 3449 |

Chi tiết phép đo nằm tại [`benchmark_report.md`](benchmark_report.md). Trace của cả hai
kiến trúc nằm tại `benchmark_traces.json`.

## 7. Phân tích kết quả

Single-agent nhanh hơn 3.503 giây và multi-agent chậm hơn khoảng 1.65 lần. Multi-agent
dùng tổng token cao hơn khoảng 3.60 lần vì phải truyền context qua ba stage và thực
hiện nhiều provider calls. Đây là overhead trực tiếp của việc phân rã nhiệm vụ.

Hai kiến trúc đạt cùng quality heuristic và citation coverage. Kết quả này cho thấy
multi-agent chưa tạo lợi thế đo được về chất lượng trong query hiện tại. Tuy nhiên,
multi-agent cung cấp trace chi tiết và phân tách responsibility nên dễ audit hơn. Nếu
Researcher tìm nguồn yếu hoặc Writer bỏ citation, lỗi có thể được gắn với đúng stage.

Quality score 10/10 không nên được hiểu là câu trả lời hoàn hảo. Heuristic chủ yếu đo
answer completeness, phần Sources, citation coverage và trạng thái lỗi. Để đánh giá
semantic quality, cần peer review hoặc LLM-as-judge có rubric riêng và kiểm tra chéo.

## 8. Failure modes và cách khắc phục

Failure mode chính gồm provider timeout, rate limit, search trả rỗng, citation thiếu,
routing loop và context loss qua handoff. Hệ thống khắc phục bằng timeout, retry,
backoff, validation, max iterations, shared state và fallback answer.

Ví dụ, nếu Researcher không lấy được nguồn sau retry, workflow ghi error vào trace và
tạo research note thể hiện limitation. Analyst và Writer có thể tiếp tục với partial
context, hoặc final answer được đánh dấu là partial result. Cơ chế này ưu tiên khả năng
giải thích lỗi thay vì che giấu failure.

Phân tích đầy đủ nằm tại [`failure_modes.md`](../docs/failure_modes.md).

## 9. Khi nào nên dùng multi-agent?

Nên dùng multi-agent khi task có nhiều stage chuyên biệt, cần sources, cần review bằng
chứng hoặc cần trace để audit. Ví dụ phù hợp gồm research report dài, due diligence,
tổng hợp tài liệu đa nguồn và workflow cần tách người tìm kiếm khỏi người đánh giá.

Không nên dùng multi-agent cho câu hỏi ngắn, task có một bước rõ ràng hoặc hệ thống
nhạy cảm với latency và token cost. Trong các trường hợp này, orchestration overhead
có thể lớn hơn lợi ích của việc phân vai.

## 10. Hạn chế và hướng phát triển

- Chạy benchmark với cả ba query trong `configs/lab_default.yaml`.
- Lặp mỗi query nhiều lần để báo cáo mean, median và variance.
- Cấu hình Tavily để đánh giá web search thực tế.
- Bổ sung peer-review score hoặc LLM judge cho semantic quality.
- Đo claim-level citation correctness thay vì chỉ URL coverage.
- Bổ sung estimated cost theo usage API hoặc pricing snapshot có ngày hiệu lực.
- Xuất trace sang LangSmith, Langfuse hoặc OpenTelemetry khi cần dashboard.

## 11. Kết luận

Project đã hoàn thiện hai luồng single-agent và multi-agent, có provider thật, shared
state, routing, guardrails, trace, tests và benchmark. Trong thí nghiệm hiện tại,
single-agent hiệu quả hơn về latency và tokens; multi-agent có lợi thế về khả năng quan
sát, phân vai và debug. Việc chọn kiến trúc nên dựa trên độ phức tạp của task thay vì
mặc định cho rằng nhiều agent luôn tốt hơn.

## 12. Deliverables

- Source code và tests trong GitHub repo cá nhân.
- `reports/benchmark_report.md`: benchmark single-agent và multi-agent.
- `reports/benchmark_traces.json`: trace dùng để chụp screenshot.
- `docs/failure_modes.md`: failure mode và cách khắc phục.
- `docs/design_template.md`: thiết kế roles, shared state, routing và benchmark plan.
