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

# Set to track already written proxies
written_proxies = set(load_proxies("vproxies.txt"))

# Save a proxy to vproxies.txt
def save_valid_proxy(proxy):
    if proxy not in written_proxies:
        with open("vproxies.txt", "a") as file:
            file.write(proxy + "\n")
        written_proxies.add(proxy)  # Add to the set

# Test a single proxy
def test_proxy(proxy, valid_proxies):
    try:
        response = requests.get("https://www.google.com", proxies={"http": proxy, "https": proxy}, timeout=10)
        if response.status_code == 200:
            print(f"Proxy {proxy} is working.")
            valid_proxies.append(proxy)
            save_valid_proxy(proxy)  # Save dynamically
            return proxy
    except Exception as e:
        print(f"Proxy {proxy} failed. Error: {e}")
    return None

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
                driver.quit()
                time.sleep(random.uniform(3, 7))
            except Exception as link_error:
                print(f"Error visiting {link} with Proxy {proxy}: {link_error}")
        driver.quit()
    except Exception as proxy_error:
        print(f"Error with Proxy {proxy}: {proxy_error}")

# Main execution
def main():
    links = load_links()
    untested_proxies = load_proxies("proxies.txt")
    valid_proxies = load_proxies("vproxies.txt")

    # Filter out already tested proxies from untested proxies
    untested_proxies = [proxy for proxy in untested_proxies if proxy not in written_proxies]

    if not untested_proxies and not valid_proxies:
        print("No proxies available. Exiting.")
        return

    with ThreadPoolExecutor(max_workers=20) as executor:
        # Test proxies if available
        if untested_proxies:
            print("Testing new proxies...")
            future_to_proxy = {executor.submit(test_proxy, proxy, valid_proxies): proxy for proxy in untested_proxies}

            # Start browsing dynamically as proxies are validated
            for future in as_completed(future_to_proxy):
                proxy = future.result()
                if proxy:  # If a proxy is valid
                    executor.submit(browse_with_proxy, proxy, links)

        # Direct browsing if no new proxies are available
        if not untested_proxies and valid_proxies:
            print("No new proxies to test. Using valid proxies for browsing.")
            for proxy in valid_proxies:
                executor.submit(browse_with_proxy, proxy, links)

        # Wait until all tasks are complete
        executor.shutdown(wait=True)

    if not untested_proxies:
        print("Finished operation: No more proxies to test.")
    else:
        print("Finished operation: Browsing completed.")

if __name__ == "__main__":
    main()
