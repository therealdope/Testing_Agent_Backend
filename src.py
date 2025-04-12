# testing website and figma links
# https://boldo-website-template.vercel.app
# TrZ4dDq2WqtxekYp9vUWce
import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (StaleElementReferenceException,
                                      ElementClickInterceptedException,
                                      ElementNotInteractableException,
                                      TimeoutException)

import os
import subprocess
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import google.generativeai as genai
import os
import json
import requests
import google.generativeai as genai
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from colorama import Fore, Style
import re
from  dotenv import load_dotenv

load_dotenv()


class WebsiteExplorer:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-logging")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome(options=options)
        self.history = []
        self.click_counter = 0
        self.max_journey_length = 9  # Increased limit for more exploration
        self.max_retries = 3 
        self.output=""
        self.visited=[]
        self.figma_code=""

    def figma_testing(self,url):

        # ----------------------------------
        # Configuration & API Keys
        # ----------------------------------
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        FIGMA_TOKEN = os.getenv("FIGMA_API_KEY")
        FIGMA_FILE_ID = self.figma_code

        # ----------------------------------
        # Figma Data Fetcher
        # ----------------------------------
        class FigmaDataFetcher:
            """Fetches Figma file data using the Figma API."""
            def __init__(self, token, file_id):
                self.token = token
                self.file_id = file_id

            def fetch_file(self):
                url = f"https://api.figma.com/v1/files/{self.file_id}"
                headers = {"X-Figma-Token": self.token}
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"Error fetching Figma data: {response.status_code} {response.text}")

        # ----------------------------------
        # Figma Data Extractor
        # ----------------------------------
        class FigmaDataExtractor:
            """
            Recursively extracts detailed component information from Figma design data.
            Focuses on visual, textual, and layout properties that are critical for testing.
            """
            def __init__(self, figma_data):
                self.figma_data = figma_data
                self.layers = {}

            def extract(self):
                if "document" not in self.figma_data:
                    raise Exception("Invalid Figma file structure")
                pages = self.figma_data["document"].get("children", [])
                for page in pages:
                    page_name = page.get("name", "Unnamed Page")
                    self.layers[page_name] = []
                    for node in page.get("children", []):
                        self._process_node(node, page_name, parent="Root", depth=0, path=[])
                return self.layers

            def _process_node(self, node, page_name, parent, depth, path):
                node_path = path + [node.get("name", "Unnamed")]
                layer_info = {
                    "name": node.get("name", "Unnamed"),
                    "id": node.get("id", "unknown-id"),
                    "type": node.get("type"),
                    "parent": parent,
                    "depth": depth,
                    "path": "/".join(node_path),
                    "visible": node.get("visible", True),
                    "opacity": node.get("opacity", 1.0),
                    "fills": [],
                    "strokes": [],
                    "effects": node.get("effects", []),
                    "layout": {
                        "constraints": node.get("constraints", {}),
                        "padding": {
                            "left": node.get("paddingLeft", 0),
                            "right": node.get("paddingRight", 0),
                            "top": node.get("paddingTop", 0),
                            "bottom": node.get("paddingBottom", 0)
                        }
                    },
                    "position": node.get("absoluteBoundingBox", {}),
                    "content": {
                        "text": node.get("characters", None),
                        "textStyle": node.get("style", {}) if node.get("type") == "TEXT" else {}
                    },
                    "component_properties": node.get("componentProperties", {}),
                    "component_id": node.get("componentId", None),
                    "instance_id": node.get("instanceId", None),
                    "potential_role": None
                }

                # Extract fill details if available
                if "fills" in node and isinstance(node["fills"], list):
                    for fill in node["fills"]:
                        if isinstance(fill, dict):
                            fill_info = {"type": fill.get("type")}
                            if "color" in fill:
                                color = fill["color"]
                                fill_info.update({
                                    "r": color.get("r"),
                                    "g": color.get("g"),
                                    "b": color.get("b"),
                                    "a": color.get("a", 1)
                                })
                            if "gradientStops" in fill:
                                fill_info["gradientStops"] = fill["gradientStops"]
                            layer_info["fills"].append(fill_info)

                # Extract stroke details if available
                if "strokes" in node and isinstance(node["strokes"], list):
                    for stroke in node["strokes"]:
                        if isinstance(stroke, dict):
                            stroke_info = {"type": stroke.get("type")}
                            if "color" in stroke:
                                color = stroke["color"]
                                stroke_info.update({
                                    "r": color.get("r"),
                                    "g": color.get("g"),
                                    "b": color.get("b"),
                                    "a": color.get("a", 1)
                                })
                            layer_info["strokes"].append(stroke_info)

                # Basic heuristics for inferring a component's role
                if node.get("type") == "RECTANGLE":
                    pos = layer_info.get("position", {})
                    w = pos.get("width", 0)
                    h = pos.get("height", 0)
                    if w > 0 and h > 0:
                        if w < 200 and h < 60:
                            layer_info["potential_role"] = "button"
                        elif (w / (h if h else 1)) > 3:
                            layer_info["potential_role"] = "input_field"
                        else:
                            layer_info["potential_role"] = "container"
                    else:
                        layer_info["potential_role"] = "unknown_rectangle"

                if node.get("type") == "TEXT":
                    text_lower = node.get("characters", "").lower()
                    font_size = layer_info["content"]["textStyle"].get("fontSize", 0)
                    if font_size > 24:
                        layer_info["potential_role"] = "heading"
                    elif any(keyword in text_lower for keyword in ["submit", "login", "sign in", "register", "send"]):
                        layer_info["potential_role"] = "button_label"
                    elif any(keyword in text_lower for keyword in ["username", "email", "password", "name"]):
                        layer_info["potential_role"] = "input_label"
                    else:
                        layer_info["potential_role"] = "body_text"

                self.layers[page_name].append(layer_info)

                for child in node.get("children", []):
                    self._process_node(child, page_name, parent=node.get("name", "Unnamed"), depth=depth+1, path=node_path)

        # ----------------------------------
        # Gemini Analyzer with Three-Stage Processing
        # ----------------------------------
        class GeminiAnalyzer:
            """
            Uses Gemini API to analyze Figma components in three stages:
            1. Summarize the main sections and important components.
            2. Improve the summary into a comprehensive JSON structure.
            3. Filter and optimize the structure to include only components critical for testing.
            """
            def __init__(self, model_name="gemini-1.5-pro-latest"):
                self.model_name = model_name
                self.model = genai.GenerativeModel(model_name)

            def summarize_components(self, figma_details):
                prompt = (
                    "You are an expert UI designer and QA engineer. Based on the following Figma design data (in JSON format), "
                    "identify the main sections of the webpage (e.g., header, footer, homepage, sidebar, etc.) and list only the important components in each section. "
                    "For example, if the header contains 4 menu items, list 'header' with those 4 items. Provide a summary that details each section and its key components, "
                    "including component names and their brief roles. Output the result as a JSON array of sections with nested components.\n\n"
                    "Figma data:\n" + json.dumps(figma_details, indent=2)[:50000]
                )
                response = self.model.generate_content(prompt)
                return response.text if response and response.text else "No summary returned from Gemini API."

            def improve_summary_structure(self, summary):
                prompt = (
                    "You are an expert UI designer and QA engineer. Based on the summary of webpage components provided below, "
                    "improve the summary and output a comprehensive JSON structure for each important UI component. "
                    "For every component, include the following keys:\n"
                    '  "id": "Component ID",\n'
                    '  "name": "Component Name",\n'
                    '  "type": "Component Type (e.g., Primary Button, Text Input)",\n'
                    '  "visualProperties": { "size": { "width": "estimated value", "height": "estimated value" }, "color": { "background": "estimated value", "border": "estimated value", "text": "estimated value" }, "position": { "x": "estimated value", "y": "estimated value" } },\n'
                    '  "functionalRole": "Description of functionality",\n'
                    '  "prototypeBehavior": { "onEvent": "Behavior details" },\n'
                    '  "parent": "Parent component name or ID",\n'
                    '  "children": [],\n'
                    '  "selectorStrategy": "A recommended CSS or XPath selector",\n'
                    '  "testCases": [ { "description": "Test case description", "input": "Test input", "expected": "Expected output" } ]\n\n'
                    "Ensure the output is a valid JSON object with a key 'components' mapping to an array of component objects. "
                    "Do not include any extra text.\n\n"
                    "Summary:\n" + summary
                )
                response = self.model.generate_content(prompt)
                return response.text if response and response.text else "No detailed breakdown returned from Gemini API."

            def finalize_testing_components(self, improved_summary):
                prompt = (
                    "You are an expert QA engineer. Based on the comprehensive JSON structure of UI components provided below, "
                    "filter and optimize the list to include only those components that are critical for automated testing of a website. "
                    "Exclude decorative or non-interactive components. For each component that is kept, ensure that its JSON structure is correct and includes "
                    "all necessary keys (id, name, type, visualProperties, functionalRole, prototypeBehavior, parent, children, selectorStrategy, and testCases). "
                    "Output the final JSON structure under a key 'components'.\n\n"
                    "Detailed Breakdown:\n" + improved_summary
                )
                response = self.model.generate_content(prompt)
                return response.text if response and response.text else "No final testing breakdown returned from Gemini API."

        # ----------------------------------
        print("\n===== COMBINED FIGMA COMPONENT ANALYZER =====\n")

        # Step 1: Fetch Figma data
        fetcher = FigmaDataFetcher(FIGMA_TOKEN, FIGMA_FILE_ID)
        try:
            figma_data = fetcher.fetch_file()
        except Exception as e:
            print(f"Error: {e}")

        # Step 2: Extract detailed design information (Figma abstraction is not printed)
        extractor = FigmaDataExtractor(figma_data)
        figma_details = extractor.extract()

        # Step 3: Stage 1 - Generate a summary of key webpage components using Gemini
        while True:
            try:
                analyzer = GeminiAnalyzer()
                summary = analyzer.summarize_components(figma_details)

                # Stage 2 - Improve summary into a detailed, structured JSON output
                improved_summary = analyzer.improve_summary_structure(summary)

                # Stage 3 - Finalize and optimize for testing: include only test-critical components in valid JSON format
                final_breakdown = analyzer.finalize_testing_components(improved_summary)
                # print(final_breakdown)
                index = final_breakdown[9:].find("```\n")
                if index != -1:
                    index += 9  # Adjust for the slice offset

                final_breakdown=final_breakdown[:index].strip("```json\n")
                # print(final_breakdown)
                final_breakdown=json.loads(final_breakdown)
                break
            except:
                print(f"Error: {e}. Retrying...")
                time.sleep(1)  # Wait for a second before retrying

        ################### I have final_breakdown from here #######################
        # Mock Figma Components (Replace with actual Figma API data)
        FIGMA_COMPONENTS = final_breakdown["components"]

        def hex_to_rgb(hex_color):
            """Convert HEX color to RGB string"""
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 3:
                hex_color = ''.join([c * 2 for c in hex_color])
            return f"rgb({int(hex_color[0:2], 16)}, {int(hex_color[2:4], 16)}, {int(hex_color[4:6], 16)})"

        def normalize_color(color):
            """Normalize color values to RGB format"""
            if color.lower() == "transparent":
                return "rgba(0, 0, 0, 0)"
            if color.startswith("#"):
                return hex_to_rgb(color)
            if color == "none":
                return "rgba(0, 0, 0, 0)"
            return color.lower()

        def get_element_xpath(driver, element):
            """Calculate the full XPath of a web element using JavaScript."""
            xpath = driver.execute_script(
                """
                function absoluteXPath(element) {
                    var comp, comps = [];
                    var parent = null;
                    var xpath = '';
                    var getPos = function(element) {
                        var position = 1, curNode;
                        if (element.nodeType == Node.ATTRIBUTE_NODE) {
                            return null;
                        }
                        for (curNode = element.previousSibling; curNode; curNode = curNode.previousSibling) {
                            if (curNode.nodeName == element.nodeName)
                                ++position;
                        }
                        return position;
                    }
                    if (element instanceof Document)
                        return '/';
                    for (; element && !(element instanceof Document); element = element.nodeType === Node.ATTRIBUTE_NODE ? element.ownerElement : element.parentNode) {
                        comp = {};
                        switch (element.nodeType) {
                            case Node.TEXT_NODE:
                                comp.name = 'text()';
                                break;
                            case Node.ATTRIBUTE_NODE:
                                comp.name = '@' + element.nodeName;
                                break;
                            case Node.PROCESSING_INSTRUCTION_NODE:
                                comp.name = 'processing-instruction()';
                                break;
                            case Node.COMMENT_NODE:
                                comp.name = 'comment()';
                                break;
                            case Node.ELEMENT_NODE:
                                comp.name = element.nodeName;
                                break;
                        }
                        comp.position = getPos(element);
                        comps.push(comp);
                    }
                    for (var i = comps.length - 1; i >= 0; i--) {
                        comp = comps[i];
                        xpath += '/' + comp.name.toLowerCase();
                        if (comp.position !== null) {
                            xpath += '[' + comp.position + ']';
                        }
                    }
                    return xpath;
                }
                return absoluteXPath(arguments[0]);
                """, element)
            return xpath

        def scrape_website(url):
            """Scrape website elements using Selenium and include their XPath."""
            driver = webdriver.Chrome()
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            elements = []
            selectors = ["img", "button", "h1", "h2", "h3", "nav", "a", "input"]
            
            for selector in selectors:
                try:
                    found_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in found_elements:
                        try:
                            location = element.location
                            size = element.size
                            styles = {
                                "background": element.value_of_css_property("background-color"),
                                "border": element.value_of_css_property("border-color"),
                                "color": element.value_of_css_property("color"),
                                "fontSize": element.value_of_css_property("font-size"),
                                "text": element.text.strip() if element.text else ""
                            }
                            element_type = selector.upper() if selector in ("h1", "h2", "h3") else selector.capitalize()
                            xpath = get_element_xpath(driver, element)
                            
                            element_data = {
                                "selector": element.get_attribute("class") or selector,
                                "type": element_type,
                                "text": styles["text"],
                                "xpath": xpath,
                                "visualProperties": {
                                    "size": {"width": size["width"], "height": size["height"]},
                                    "color": {
                                        "background": styles["background"],
                                        "border": styles["border"],
                                        "text": styles["color"]
                                    },
                                    "position": {"x": location["x"], "y": location["y"]},
                                    "fontSize": styles["fontSize"]
                                }
                            }
                            elements.append(element_data)
                        except Exception as e:
                            print(f"{Fore.YELLOW}Warning: Could not process {selector} - {e}{Style.RESET_ALL}")
                            continue
                except WebDriverException as e:
                    print(f"{Fore.YELLOW}Warning: Could not find {selector} elements - {e}{Style.RESET_ALL}")
                    continue
            
            driver.quit()
            print(elements)
            return elements

        def calculate_similarity(figma_comp, web_element):
            """Calculate similarity score between components"""
            score = 0
            
            if figma_comp["type"].lower() == web_element["type"].lower():
                score += 20
            
            if "size" in figma_comp["visualProperties"] and "size" in web_element["visualProperties"]:
                figma_size = figma_comp["visualProperties"]["size"]
                web_size = web_element["visualProperties"]["size"]
                try:
                    if abs(figma_size["width"] - web_size["width"]) <= 10:
                        score += 15
                    if abs(figma_size["height"] - web_size["height"]) <= 10:
                        score += 15
                except Exception as e:
                    print("Size comparison error:", e)
            
            figma_colors = figma_comp["visualProperties"]["color"]
            web_colors = web_element["visualProperties"]["color"]
            if normalize_color(figma_colors["background"]) == normalize_color(web_colors["background"]):
                score += 10
            if normalize_color(figma_colors["text"]) == normalize_color(web_colors["text"]):
                score += 10
            
            if "position" in figma_comp["visualProperties"] and "position" in web_element["visualProperties"]:
                figma_pos = figma_comp["visualProperties"]["position"]
                web_pos = web_element["visualProperties"]["position"]
                try:
                    if abs(figma_pos["x"] - web_pos["x"]) <= 20:
                        score += 10
                    if abs(figma_pos["y"] - web_pos["y"]) <= 20:
                        score += 10
                except Exception as e:
                    print("Position comparison error:", e)
            
            if "text" in web_element and "name" in figma_comp:
                if figma_comp["name"].lower() in web_element["text"].lower():
                    score += 20
            
            return score

        def highlight_and_screenshot(driver, xpath, figma_id, screenshots_folder):
            """Scroll element into view, highlight it with a red border, and take a screenshot."""
            try:
                element = driver.find_element(By.XPATH, xpath)
                # Scroll element into view
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                # Apply a strong red border; you can also add '!important' style by resetting the style attribute if needed.
                driver.execute_script("arguments[0].style.border='3px solid red';", element)
                # Allow some time for the style to apply
                time.sleep(5)
                screenshot_path = os.path.join(screenshots_folder, f"{figma_id}_highlight.png")
                element.screenshot(screenshot_path)
                print(f"Screenshot for {figma_id} saved to {screenshot_path}")
            except Exception as e:
                print(f"{Fore.YELLOW}Could not highlight/screenshot element for {figma_id} - {e}{Style.RESET_ALL}")

        """Main execution flow"""
        website_url = url

        print(f"{Fore.CYAN}Scraping website...{Style.RESET_ALL}")
        website_elements = scrape_website(website_url)

        matches = []
        non_matches = []

        for figma_comp in FIGMA_COMPONENTS:
            best_match = {"score": 0, "element": None}
            for web_el in website_elements:
                current_score = calculate_similarity(figma_comp, web_el)
                if current_score > best_match["score"]:
                    best_match = {
                        "score": current_score,
                        "element": web_el,
                        "details": {
                            "size": web_el["visualProperties"]["size"],
                            "position": web_el["visualProperties"]["position"]
                        }
                    }
            if best_match["score"] >= 60:
                matches.append({
                    "figma_id": figma_comp["id"],
                    "web_selector": best_match["element"]["selector"],
                    "similarity_score": best_match["score"],
                    "details": best_match["details"]
                })
            else:
                non_matches.append({
                    "figma_id": figma_comp["id"],
                    "reason": f"No match found (Best score: {best_match['score']}/100)",
                    "xpath": best_match["element"]["xpath"] if best_match["element"] else None
                })

        print(f"\n{Fore.GREEN}=== Matches ==={Style.RESET_ALL}")
        for match in matches:
            print(f"{Fore.GREEN}• {match['figma_id']} => {match['web_selector']}")
            print(f"  Score: {match['similarity_score']}/100")
            print(f"  Size: {match['details']['size']}")
            print(f"  Position: {match['details']['position']}{Style.RESET_ALL}")

        print(f"\n{Fore.RED}=== Non-Matches ==={Style.RESET_ALL}")
        for non_match in non_matches:
            print(f"{Fore.RED}• {non_match['figma_id']}: {non_match['reason']}{Style.RESET_ALL}")

        # ------------- Highlighting Unmatched Components & Taking Screenshots -------------
        if non_matches:
            # Create a folder for screenshots if it doesn't exist
            screenshots_folder = "screenshots"
            os.makedirs(screenshots_folder, exist_ok=True)
            
            driver = webdriver.Chrome()
            driver.get(website_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            for non in non_matches:
                xpath = non.get("xpath")
                if xpath:
                    highlight_and_screenshot(driver, xpath, non["figma_id"], screenshots_folder)
            
            # Optionally, also take a full-page screenshot after highlighting.
            time.sleep(5)
            full_screenshot = os.path.join(screenshots_folder, "full_page_highlight.png")
            driver.save_screenshot(full_screenshot)
            print(f"Full page screenshot saved to {full_screenshot}")
            
            # Optionally, keep the browser open for a short period.
            time.sleep(10)
            driver.quit()

    def run_functional_tests(self,TARGET_URL):
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Replace with your actual Gemini API key
        SELECTED_COMPONENTS = ['forms', 'text_fields', 'checkboxes', 'radio_buttons', 'buttons', 'links', 'images']
        OUTPUT_COMPONENTS_FILE = "./extracted_components.json"
        OUTPUT_TEST_FILE = "./generated_test.py"
        OUTPUT_LOG_FILE="./functional_tests_log.txt"
        HEADLESS_MODE = True
        WAIT_TIME = 3  # Seconds to wait for page load

        def extract_components(url, selected_components):
            """Extract components from a webpage"""
            print(f"Extracting components from {url}...")
            
            # Setup Chrome options
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            
            service = Service()
            service.creation_flags = 0        
            # Use webdriver manager to handle ChromeDriver installation
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                driver.get(url)
                # Wait for page to load completely
                time.sleep(WAIT_TIME)
                
                # Get page title for reference
                page_title = driver.title
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                components = {
                    "url": url,
                    "page_title": page_title,
                    "components": {}
                }
                
                if 'forms' in selected_components:
                    components["components"]['forms'] = []
                    for form in soup.find_all('form'):
                        form_data = {
                            'action': form.get('action'),
                            'method': form.get('method', 'get'),
                            'id': form.get('id', ''),
                            'class': form.get('class', ''),
                            'inputs': []
                        }
                        
                        # Get all form elements
                        for input_tag in form.find_all(['input', 'select', 'textarea', 'button']):
                            if input_tag.name == 'input':
                                input_data = {
                                    'element_type': 'input',
                                    'name': input_tag.get('name', ''),
                                    'id': input_tag.get('id', ''),
                                    'type': input_tag.get('type', 'text'),
                                    'value': input_tag.get('value', ''),
                                    'placeholder': input_tag.get('placeholder', ''),
                                    'required': input_tag.get('required') is not None,
                                    'xpath': get_xpath(input_tag)
                                }
                            elif input_tag.name == 'select':
                                options = [{'value': opt.get('value', ''), 'text': opt.text.strip()} 
                                        for opt in input_tag.find_all('option')]
                                input_data = {
                                    'element_type': 'select',
                                    'name': input_tag.get('name', ''),
                                    'id': input_tag.get('id', ''),
                                    'options': options,
                                    'required': input_tag.get('required') is not None,
                                    'xpath': get_xpath(input_tag)
                                }
                            elif input_tag.name == 'textarea':
                                input_data = {
                                    'element_type': 'textarea',
                                    'name': input_tag.get('name', ''),
                                    'id': input_tag.get('id', ''),
                                    'placeholder': input_tag.get('placeholder', ''),
                                    'required': input_tag.get('required') is not None,
                                    'xpath': get_xpath(input_tag)
                                }
                            elif input_tag.name == 'button':
                                input_data = {
                                    'element_type': 'button',
                                    'name': input_tag.get('name', ''),
                                    'id': input_tag.get('id', ''),
                                    'type': input_tag.get('type', 'submit'),
                                    'text': input_tag.text.strip(),
                                    'xpath': get_xpath(input_tag)
                                }
                            
                            form_data['inputs'].append(input_data)
                        
                        components["components"]['forms'].append(form_data)
                
                # Add specific element types with detailed information
                if 'text_fields' in selected_components:
                    components["components"]['text_fields'] = [{
                        'name': input_tag.get('name', ''),
                        'id': input_tag.get('id', ''),
                        'placeholder': input_tag.get('placeholder', ''),
                        'required': input_tag.get('required') is not None,
                        'xpath': get_xpath(input_tag),
                        'css_selector': f"input[type='text'][id='{input_tag.get('id', '')}']" if input_tag.get('id') else f"input[type='text'][name='{input_tag.get('name', '')}']"
                    } for input_tag in soup.find_all('input', type='text')]
                
                if 'checkboxes' in selected_components:
                    components["components"]['checkboxes'] = [{
                        'name': input_tag.get('name', ''),
                        'id': input_tag.get('id', ''),
                        'value': input_tag.get('value', ''),
                        'checked': input_tag.get('checked') is not None,
                        'xpath': get_xpath(input_tag),
                        'css_selector': f"input[type='checkbox'][id='{input_tag.get('id', '')}']" if input_tag.get('id') else f"input[type='checkbox'][name='{input_tag.get('name', '')}']"
                    } for input_tag in soup.find_all('input', type='checkbox')]
                
                if 'radio_buttons' in selected_components:
                    components["components"]['radio_buttons'] = [{
                        'name': input_tag.get('name', ''),
                        'id': input_tag.get('id', ''),
                        'value': input_tag.get('value', ''),
                        'checked': input_tag.get('checked') is not None,
                        'xpath': get_xpath(input_tag),
                        'css_selector': f"input[type='radio'][id='{input_tag.get('id', '')}']" if input_tag.get('id') else f"input[type='radio'][name='{input_tag.get('name', '')}'][value='{input_tag.get('value', '')}']"
                    } for input_tag in soup.find_all('input', type='radio')]
                
                if 'buttons' in selected_components:
                    components["components"]['buttons'] = [{
                        'text': btn.text.strip(),
                        'id': btn.get('id', ''),
                        'type': btn.get('type', 'button'),
                        'xpath': get_xpath(btn),
                        'css_selector': f"button[id='{btn.get('id', '')}']" if btn.get('id') else f"button:contains('{btn.text.strip()}')"
                    } for btn in soup.find_all('button')]
                
                if 'links' in selected_components:
                    components["components"]['links'] = [{
                        'href': a.get('href', ''),
                        'text': a.text.strip(),
                        'id': a.get('id', ''),
                        'xpath': get_xpath(a),
                        'css_selector': f"a[id='{a.get('id', '')}']" if a.get('id') else f"a[href='{a.get('href', '')}']"
                    } for a in soup.find_all('a') if a.text.strip()]
                
                if 'images' in selected_components:
                    components["components"]['images'] = [{
                        'src': img.get('src', ''),
                        'alt': img.get('alt', ''),
                        'id': img.get('id', ''),
                        'xpath': get_xpath(img),
                        'css_selector': f"img[id='{img.get('id', '')}']" if img.get('id') else f"img[src='{img.get('src', '')}']"
                    } for img in soup.find_all('img')]
                
                component_count = sum(len(components['components'].get(comp_type, [])) for comp_type in components['components'])
                print(f"Successfully extracted {component_count} components from {url}")
                return components
            
            except Exception as e:
                error_message = f"Error extracting components: {str(e)}"
                print(error_message)
                return {"error": error_message, "url": url}
            
            finally:
                driver.quit()

        def get_xpath(element):
            """Generate a simple XPath for the element based on its attributes"""
            if element.get('id'):
                return f"//{element.name}[@id='{element.get('id')}']"
            elif element.get('name'):
                return f"//{element.name}[@name='{element.get('name')}']"
            elif element.name == 'a' and element.text.strip():
                return f"//a[contains(text(), '{element.text.strip()}')]"
            elif element.name == 'button' and element.text.strip():
                return f"//button[contains(text(), '{element.text.strip()}')]"
            else:
                return f"//{element.name}"

        def generate_test_cases(components):
            """Generate test cases using Gemini API"""
            print("Generating test cases using Gemini API...")
            
            # Configure Gemini API
            api_key = GOOGLE_API_KEY
            if not api_key:
                # Try to get from environment
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    print("Error: No Gemini API key provided. Please set the GOOGLE_API_KEY variable.")
                    return "# Error: No Gemini API key provided."
            
            genai.configure(api_key=api_key)
            
            # Initialize the Gemini Model
            model = genai.GenerativeModel("gemini-1.5-pro-latest")
            
            # Format a clearer prompt with specific instructions
            prompt = f"""
        Generate comprehensive Python Selenium test cases for the webpage with the following components:

        URL: {components['url']}
        Page Title: {components['page_title']}

        Component Details:
        {json.dumps(components['components'], indent=2)}

        Create well-structured test cases that:
        1. Define a proper test class with setup and teardown methods
        2. Include tests for each component type found on the page
        3. Use proper locators (ID, XPath, CSS selectors) provided in the component data
        4. Include validation steps to verify expected behavior
        5. Handle potential errors gracefully
        6. Use page object model pattern if appropriate

        Please include imports for all necessary Selenium modules and classes.
        without comments or explanations.
        """
            
            try:
                response = model.generate_content([prompt])
                
                test_code = response.text.strip()
                
                # Clean up the code if it's wrapped in markdown code blocks
                if test_code.startswith("```python"):
                    test_code = test_code[9:]
                if test_code.endswith("```"):
                    test_code = test_code[:-3]
                
                # Add imports if they're missing
                if "from selenium import webdriver" not in test_code:
                    test_code = """from selenium import webdriver
                                    from selenium.webdriver.chrome.service import Service
                                    from selenium.webdriver.chrome.options import Options
                                    from selenium.webdriver.common.by import By
                                    from selenium.webdriver.support.ui import WebDriverWait
                                    from selenium.webdriver.support import expected_conditions as EC
                                    from selenium.webdriver.support.ui import Select
                                    from webdriver_manager.chrome import ChromeDriverManager
                                    import unittest
                                    import time
                                """ + test_code
                
                # Add auto-run code if not present
                if "__name__ == '__main__'" not in test_code:
                    test_code += "\n\nif __name__ == '__main__':\n    unittest.main()"
                
                print("Test cases generated successfully.")
                return test_code.strip("")
            
            except Exception as e:
                error_message = f"Error generating test cases: {str(e)}"
                print(error_message)
                return f"# {error_message}\n\n# Please check your Gemini API key and try again."


        """Main function to orchestrate the automated process"""

        # Validate URL
        url = TARGET_URL
        if not url.startswith("http"):
            url = "https://" + url
            print(f"Updated URL to: {url}")

        # Extract components
        result = extract_components(url, SELECTED_COMPONENTS)

        # Save components to JSON file for reference
        with open(OUTPUT_COMPONENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"Components saved to {OUTPUT_COMPONENTS_FILE}")

        # Generate test cases
        test_code = generate_test_cases(result)

        # Save the generated test cases to a file
        with open(OUTPUT_TEST_FILE, "w", encoding="utf-8") as f:
            f.write(test_code + "\n")

        print(f"Test cases saved in {OUTPUT_TEST_FILE}")
        print(f"Run the tests with: python {OUTPUT_TEST_FILE}")

        result = subprocess.run(["python", OUTPUT_TEST_FILE], capture_output=True, text=True)

        with open(OUTPUT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"FUNCTIONAL TESTS ON {TARGET_URL}:\n{result.stderr}\n\n")

    def find_clickable_elements(self):
        # Skip hidden elements and inputs that don't trigger navigation
        selectors = [
            "button:not([disabled])", 
            "a[href]", 
            "[role='button']:not([disabled])",
            "input[type='submit']:not([disabled])",
            "[onclick]:not(input):not(textarea):not(select)",
            ".btn:not([disabled])",
            "[tabindex]:not([tabindex='-1'])"
        ]
        return self.driver.find_elements(By.CSS_SELECTOR, ", ".join(selectors))

    def handle_popups(self):
        try:
            alert = self.driver.switch_to.alert
            self.output+=f"🐭 Found alert: {alert.text[:50]}... dismissing!\n"
            alert.dismiss()
            time.sleep(1)
        except:
            pass

    def get_element_info(self, element):
        try:
            return {
                "tag": element.tag_name,
                "text": element.text[:30] if element.text else "",
                "id": element.get_attribute("id") or ""
            }
        except StaleElementReferenceException:
            return {"tag": "ghost", "text": "", "id": ""}

    def try_playful_click(self, element):
        try:
            # Fun scrolling animation
            self.driver.execute_script("""
                arguments[0].scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'nearest'
                });
            """, element)
            
            # Add colorful console message
            self.output+=f"🎯 Trying to click {element.tag_name}...  "
            
            # Human-like delay with random variation
            time.sleep(random.uniform(0.3, 0.7))
            
            element.click()
            self.output+="🌈 Success!\n"
            return True, self.get_element_info(element)
        except (ElementClickInterceptedException, 
                ElementNotInteractableException,
                StaleElementReferenceException):
            try:
                self.output+="🤖 Using robot click...   "
                self.driver.execute_script("arguments[0].click();", element)
                self.output+="🎉 Second chance success!\n"
                return True, self.get_element_info(element)
            except:
                self.output+="\n💥 Click failed\n"
                return False, self.get_element_info(element)

    def explore_page(self):
        retry_count = 0
        while retry_count < self.max_retries:  
            self.handle_popups()
            original_url = self.driver.current_url
            
            try:
                elements = self.find_clickable_elements()
                random.shuffle(elements)
                self.output += f"🔍 Found {len(elements)} clickables on {original_url}\n"
                
                for element in elements:
                    if self.click_counter >= self.max_journey_length:
                        return False

                    success, element_info = self.try_playful_click(element)
                    
                    if success:
                        self.click_counter += 1
                        action_desc = self.create_action_description(element_info)
                        self.history.append({"url": original_url, "action": action_desc})
                        
                        # Check for page changes
                        try:
                            WebDriverWait(self.driver, 2).until(
                                lambda d: d.current_url != original_url or
                                EC.presence_of_element_located((By.XPATH, "//*[not(.=preceding::*)]"))
                            )
                        except TimeoutException:
                            self.output += "🔄 Page didn't change, but something might be different!\n"

                        # Check if URL changed and run tests
                        new_url = self.driver.current_url
                        if new_url != original_url:
                            self.output += f"🌐 New URL detected: {new_url}\n"
                            if (new_url not in self.visited):
                                self.visited.append(new_url)
                                self.run_functional_tests(new_url)  # CALLING THE FUNCTION HERE
                                self.figma_testing(new_url)

                        return True

                    time.sleep(random.uniform(0.5, 1.5))
                    retry_count += 1
            except Exception as e:
                self.output += f"⚠️ Unexpected error: {str(e)}\n"
                retry_count += 1
        
        # Handle back navigation and test
        if self.try_going_back():
            current_url = self.driver.current_url
            self.output += f"↩️ Navigated back to: {current_url}\n"
            if (current_url not in self.visited):
                self.visited.append(current_url)
                self.run_functional_tests(current_url)  # TEST PREVIOUS PAGE
                self.figma_testing(current_url)
            return True

        return False

    def create_action_description(self, element_info):
        description = []
        if element_info['tag']:
            description.append(f"<{element_info['tag'].upper()}>")
        if element_info['text']:
            description.append(f"'💬 {element_info['text']}'")
        if element_info['id']:
            description.append(f"(🔖 #{element_info['id']})")
        return " ".join(description)

    def try_going_back(self):
        if len(self.history) > 1:
            self.output+="⏪ Nothing interesting here - going back!\n"
            try:
                self.driver.back()
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.history.pop()
                time.sleep(2)  # Let user see the navigation
                return True
            except Exception as e:
                self.output+=f"🚨 Failed to go back: {str(e)}\n"
        return False

    def start_journey(self, start_url, figma_code):
        self.output+=f"🚀 Starting adventure at {start_url}\n"
        self.driver.get(start_url)
        self.figma_code=figma_code
        if (start_url not in self.visited):
            self.visited.append(start_url)
            self.run_functional_tests(start_url)  # INITIAL TEST
            self.figma_testing(start_url)
        self.history.append({"url": start_url, "action": "🏁 START"})
        
        while self.click_counter < self.max_journey_length:
            if not self.explore_page():
                self.output+="🛑 Adventure complete!\n"
                break
                
        self.output+="\n📜 Exploration Story:\n"
        for idx, step in enumerate(self.history):
            self.output+=f"{idx+1}. {step['action']} → 🌐 {step['url']}\n"
            
        self.output+=f"\n🎉 Total clicks: {self.click_counter}\n"
        self.driver.quit()

        with open("./responsive_tests.txt", "a", encoding="utf-8") as f:
            f.write(f"{self.output}")

        #THE BELOW CODE IS THE NO GO ZONE FOR CODERS

        # with open("./functional_tests_log.txt", "r", encoding="utf-8") as file:
        #     content = file.read()

        # prompt = (
        #             f"These are the log files of component testing. You have to format it such that even a kid can understand the log file. Preserve all the information like file paths and the log messages. E means Error on that testcase, F means Failure on that testcase and '.' means success on that test case. Format and give proper document output that can be displayed on a website. THE FOLLOWING ARE THE COMPONENT TESTING LOG FILES: {content}. THE OUTPUT FILE SHOULD NOT BE LIKE HTML BUT LIKE A STRUCTURED DOCUMENT. DO NOT GIVE COMMENTS OR EXTRA THINGS LIKE KEY IMPORVEMENTS."
                    
        #         )
        # model = genai.GenerativeModel("gemini-1.5-pro-latest")
        # response = model.generate_content(prompt)
        # with open("./functional_tests_log_2.txt", "w") as file:
        #     file.write(f"{response.text}")
        

# # Let's explore!
# explorer = WebsiteExplorer()
# explorer.start_journey("https://boldo-website-template.vercel.app","TrZ4dDq2WqtxekYp9vUWce")    #Webpage and Figma ID
if __name__ == "__main__":
    explorer = WebsiteExplorer()