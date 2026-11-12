FROM python:3.12-slim

WORKDIR /app

# 先只拷依赖清单 → 改代码时不会重装依赖（层缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再拷代码
COPY stage5_agent ./stage5_agent

EXPOSE 8010

CMD ["uvicorn", "api:app", "--app-dir", "stage5_agent", "--host", "0.0.0.0", "--port", "8010"]