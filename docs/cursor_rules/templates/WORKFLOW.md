# Hướng Dẫn Làm Việc Với Cursor

## Workflow Tổng Quan

### 1. Prompt thực hiện phân tích tasks và chia nhỏ, sau đó viết document liên quan

```
## Hoàn thành các document liên quan tới task cụ thể
Dựa vào @task_breakdown.mdc hãy phân nhỏ chi tiết [TASK ID] cho tôi Task document: @tasks.md sau đó viết Technical Design Document cho [TASK ID] theo @technical_design.md. Chỉ viết hoàn thiện document mà không thực hiện việc viết code.
```

### 2. Prompt thực hiện code cụ thể 1 task dựa vào các tài liệu sẵn có

```
  Implementation:
   Task document: <task_file>.md
   Technical Design Document: <technical_design_document>.md
   explain the approach in detail first without writing any code.
```
