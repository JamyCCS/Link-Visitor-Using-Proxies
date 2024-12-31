from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
import random
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# User-Agents List
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
]

# Load Links from File
def load_links():
    with open("links.txt", "r") as file:
        return [line.strip() for line in file if line.strip()]

# Load Proxies from File
def load_proxies(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return [line.strip() for line in file if line.strip()]
    return []

# Save proxies back to proxies.txt
def save_proxies(proxies):
    with open("proxies.txt", "w") as file:
        file.writelines([proxy + "\n" for proxy in proxies])

# Test a single proxy
def test_proxy(proxy, valid_proxies, all_proxies):
    try:
        response = requests.get("https://www.google.com", proxies={"http": proxy, "https": proxy}, timeout=10)
        if response.status_code == 200:
            print(f"Proxy {proxy} is working.")
            valid_proxies.append(proxy)
            return True
    except Exception as e:
        print(f"Proxy {proxy} failed. Error: {e}")
    return False

# Browse with a proxy
def browse_with_proxy(proxy, links):
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

                print(f"Visited {link} with Proxy: {proxy}")
                time.sleep(random.uniform(3, 7))
            except Exception as link_error:
                print(f"Error visiting {link} with Proxy {proxy}: {link_error}")
        driver.quit()
    except Exception as proxy_error:
        print(f"Error with Proxy {proxy}: {proxy_error}")

# Main execution
def main():
    links = load_links()
    all_proxies = load_proxies("proxies.txt")

    if not all_proxies:
        print("No proxies available. Exiting.")
        return

    valid_proxies = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        # Test proxies if available
        print("Testing proxies...")
        future_to_proxy = {executor.submit(test_proxy, proxy, valid_proxies, all_proxies): proxy for proxy in all_proxies}

        # Update proxies.txt dynamically as proxies are tested
        for future in as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            try:
                is_valid = future.result()
                if not is_valid:
                    all_proxies.remove(proxy)  # Remove invalid proxies dynamically
                    save_proxies(all_proxies)
                else:
                    executor.submit(browse_with_proxy, proxy, links)
            except Exception as e:
                print(f"Error processing proxy {proxy}: {e}")

        # Save remaining valid proxies back to proxies.txt
        save_proxies(valid_proxies)

    if not valid_proxies:
        print("Finished operation: No valid proxies found.")
    else:
        print("Finished operation: Browsing completed.")

if __name__ == "__main__":
    main()