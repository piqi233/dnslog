from flask import Flask, render_template, jsonify, request
from dnslib import DNSRecord, QTYPE, A
from dnslib.server import DNSServer
import sqlite3
import threading
import random
import string
from datetime import datetime

app = Flask(__name__)

# 数据库初始化
def init_db():
    conn = sqlite3.connect('dnslog.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS dns_requests
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, domain TEXT, client_ip TEXT, timestamp DATETIME)''')
    conn.commit()
    conn.close()

# 记录 DNS 请求
def log_dns_request(domain, client_ip):
    conn = sqlite3.connect('dnslog.db')
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 获取当前时间
    c.execute("INSERT INTO dns_requests (domain, client_ip, timestamp) VALUES (?, ?, ?)",
              (domain, client_ip, timestamp))
    conn.commit()
    conn.close()

# 清空 DNS 请求记录
def clear_dns_requests():
    conn = sqlite3.connect('dnslog.db')
    c = conn.cursor()
    c.execute("DELETE FROM dns_requests")
    conn.commit()
    conn.close()

# 生成随机域名
def generate_random_domain():
    letters = string.ascii_lowercase
    random_str = ''.join(random.choice(letters) for _ in range(8))
    return f"{random_str}.ns1.dnslog.xxx"  # 修改为你的域名

# DNS 请求处理器
class DNSLogger:
    def resolve(self, request, handler):
        domain = str(request.q.qname)
        client_ip = handler.client_address[0]  # 获取客户端 IP
        print(f"Received DNS request from {client_ip} for {domain}")  # 打印日志以调试
        log_dns_request(domain, client_ip)  # 记录域名和客户端 IP
        return request.reply()

# 启动 DNS 服务器
def start_dns_server():
    logger = DNSLogger()
    server = DNSServer(logger, port=53)
    server.start()

# Flask API
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/requests')
def get_requests():
    conn = sqlite3.connect('dnslog.db')
    c = conn.cursor()
    c.execute("SELECT domain, client_ip, timestamp FROM dns_requests ORDER BY timestamp DESC")
    requests = c.fetchall()
    conn.close()
    return jsonify(requests)

@app.route('/api/generate-domain', methods=['GET'])
def generate_domain():
    domain = generate_random_domain()
    return jsonify({"domain": domain})

@app.route('/api/clear-requests', methods=['POST'])
def clear_requests():
    clear_dns_requests()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    init_db()
    # 启动 DNS 服务器线程
    dns_thread = threading.Thread(target=start_dns_server)
    dns_thread.daemon = True
    dns_thread.start()
    # 启动 Flask 应用
    app.run(host='0.0.0.0', port=5000)
