from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
import random
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# List of User-Agents
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
]

# Load Proxies from File
with open("proxies.txt", "r") as file:
    proxies = [line.strip() for line in file if line.strip()]

# Load Links from File
with open("links.txt", "r") as file:
    links = [line.strip() for line in file if line.strip()]

# Function to test a single proxy
def test_proxy(proxy):
    try:
        response = requests.get("https://www.google.com", proxies={"http": proxy, "https": proxy}, timeout=5)
        if response.status_code == 200:
            print(f"Proxy {proxy} is working.")
            return proxy
    except Exception as e:
        print(f"Proxy {proxy} failed. Error: {e}")
    return None

# Function to start browsing with a proxy
def browse_with_proxy(proxy):
    try:
        user_agent = random.choice(user_agents)
        edge_options = Options()
        edge_options.add_argument(f"user-agent={user_agent}")
        edge_options.add_argument(f"--proxy-server={proxy}")
        edge_options.add_argument("--ignore-certificate-errors")

        edge_driver_path = "msedgedriver.exe"
        service = Service(edge_driver_path)

        driver = webdriver.Edge(service=service, options=edge_options)

        for link in links:
            try:
                driver.get(link)

                # Simulate Scrolling
                for _ in range(5):
                    driver.execute_script("window.scrollBy(0, 500);")
                    time.sleep(random.uniform(1, 3))
                for _ in range(5):
                    driver.execute_script("window.scrollBy(0, -500);")
                    time.sleep(random.uniform(1, 3))

                print(f"Visited {link} with User-Agent: {user_agent} and Proxy: {proxy}")
                time.sleep(random.uniform(3, 7))
            except Exception as link_error:
                print(f"Error visiting {link} with Proxy {proxy}: {link_error}")
        driver.quit()
    except Exception as proxy_error:
        print(f"Error with Proxy {proxy}: {proxy_error}")

# Main execution
def main():
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in proxies}

        # Continuously test proxies and browse
        for future in as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            try:
                result = future.result()
                if result:  # If proxy is valid
                    executor.submit(browse_with_proxy, result)
            except Exception as e:
                print(f"Error processing proxy {proxy}: {e}")
        print("Finished")

if __name__ == "__main__":
    main()