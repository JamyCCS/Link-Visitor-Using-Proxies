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

# Retry parameters
MAX_RETRIES = 3  # Number of retries before marking a proxy as failed
TIMEOUT = 20     # Timeout in seconds for each proxy test

def test_proxy(proxy):
    """Test if a proxy is working."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get("https://www.google.com", proxies={"http": proxy, "https": proxy}, timeout=TIMEOUT)
            if response.status_code == 200:
                print(f"Proxy {proxy} is working on attempt {attempt + 1}.")
                return True
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for proxy {proxy}. Error: {e}")
        time.sleep(1)  # Optional delay between retries
    return False


# Validate proxies
valid_proxies = []
for proxy in proxies:
    if test_proxy(proxy):
        valid_proxies.append(proxy)
    else:
        print(f"Proxy {proxy} failed all attempts and will be removed.")

# Save valid proxies back to file
with open("vproxies.txt", "w") as file:
    for proxy in valid_proxies:
        file.write(proxy + "\n")

print(f"Valid proxies saved: {len(valid_proxies)}")

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
        future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in valid_proxies}

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