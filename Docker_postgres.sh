#!/bin/bash
# 1) کانتینر فعلی را متوقف و حذف کنید
docker stop postgres-container
docker rm postgres-container

# 2) کانتینر را با Publish پورت بسازید
docker run --name postgres-container `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=your-postgres-password `
  -e POSTGRES_DB=gitdm `
  -p 5432:5432 `
  -v pgdata:/var/lib/postgresql/data `
  -d postgres:latest

# 3) بررسی
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
# باید چیزی مثل: 0.0.0.0:5432->5432/tcp نمایش دهد

# 4) تست از ویندوز
Test-NetConnection -ComputerName 127.0.0.1 -Port 5432
# حالا باید TcpTestSucceeded : True شود
