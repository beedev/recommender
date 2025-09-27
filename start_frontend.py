#!/usr/bin/env python3
"""
Simple HTTP server for serving the guided flow frontend on port 3000
"""

import http.server
import socketserver
import os
import sys

PORT = 3000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for API calls
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    # Change to the directory containing the HTML files
    os.chdir('/Users/bharath/Desktop/AgenticAI/Recommender')
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🌐 Frontend server starting on http://localhost:{PORT}")
        print(f"📁 Serving files from: {os.getcwd()}")
        print(f"🔧 Guided Flow: http://localhost:{PORT}/guided_flow.html")
        print(f"💬 Main Chat: http://localhost:{PORT}/frontend_prototype.html")
        print(f"📊 Health Dashboard: http://localhost:{PORT}/health_dashboard.html")
        print("\nPress Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")
            sys.exit(0)

if __name__ == "__main__":
    main()