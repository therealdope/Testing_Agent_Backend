from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from src import WebsiteExplorer
import os
import base64
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["testing-agent-skheni.vercel.app", "http://localhost:3000"],
        "methods": ["POST", "GET", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": True,
        "max_age": 3600
    }
})

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/testagent', methods=["POST"])
def test_agent():
    try:
        data = request.get_json()
        websiteurl = data.get("websiteurl")
        figmaid = data.get("figmaid")

        if not websiteurl or not figmaid:
            return jsonify({"message": "Missing required parameters"}), 400
        
        # # Remove existing output files
        # files_to_remove = [
        #     "./extracted_components.json",
        #     "./generated_test.py",
        #     "./functional_tests_log.txt",
        #     "./responsive_tests.txt"
        # ]
        
        # for file_path in files_to_remove:
        #     if os.path.exists(file_path):
        #         os.remove(file_path)
        
        # # Remove existing screenshots directory
        # screenshots_dir = "./screenshots"
        # if os.path.exists(screenshots_dir):
        #     for file in os.listdir(screenshots_dir):
        #         os.remove(os.path.join(screenshots_dir, file))
        #     os.rmdir(screenshots_dir)
        
        # Initialize WebsiteExplorer with proper Chrome setup for M1/M2 Mac
        # chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument('--no-sandbox')
        # chrome_options.add_argument('--disable-dev-shm-usage')
        # chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        # explorer = WebsiteExplorer()
        # explorer.chrome_options = chrome_options
        # explorer.start_journey(websiteurl, figmaid)
        
        # Collect test results and files
        output_data = {
            "components": None,
            "test_file": None,
            "logs": None,
            "responsive_tests": None,
            "screenshots": []
        }
        
        # Read components JSON
        try:
            with open("./extracted_components.json", "r") as f:
                output_data["components"] = f.read()
        except Exception as e:
            print(f"Error reading components: {str(e)}")

        # Read and collect all generated test files and results
        # Read components JSON
        try:
            with open("./extracted_components.json", "r") as f:
                output_data["components"] = f.read()
        except:
            pass

        # Read test file
        try:
            with open("./generated_test.py", "r") as f:
                output_data["test_file"] = f.read()
        except:
            pass

        # Read logs
        try:
            with open("./functional_tests_log.txt", "r") as f:
                output_data["logs"] = f.read()
        except:
            pass

        # Read responsive tests
        try:
            with open("./responsive_tests.txt", "r") as f:
                output_data["responsive_tests"] = f.read()
        except:
            pass

        # Read screenshots
        screenshots_dir = "./screenshots"
        if os.path.exists(screenshots_dir):
            for filename in os.listdir(screenshots_dir):
                if filename.endswith('.png'):
                    filepath = os.path.join(screenshots_dir, filename)
                    with open(filepath, "rb") as f:
                        img_data = base64.b64encode(f.read()).decode('utf-8')
                        output_data["screenshots"].append({
                            "name": filename,
                            "data": img_data
                        })

        return jsonify({
            "message": "Success",
            "data": output_data
        }), 200

    except Exception as e:
        print(f"Server Error: {str(e)}")  # Detailed error logging
        import traceback
        traceback.print_exc()  # Print full stack trace
        return jsonify({
            "message": "Server Error",
            "error": str(e),
            "type": type(e).__name__
        }), 500

if __name__ == '__main__':
    port = 5000
    app.run(host='0.0.0.0', port=port)
    