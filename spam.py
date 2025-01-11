import random
import time
import asyncio
import aiohttp
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from queue import Queue
import sys
import traceback
from datetime import datetime

# User-Agent List
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
]

# Global Exception Logging
def log_exceptions(exctype, value, tb):
    with open("error.log", "a") as log_file:
        log_file.write("".join(traceback.format_exception(exctype, value, tb)))

sys.excepthook = log_exceptions

# Log filename based on current date and time
log_filename = f"log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"

# Custom Print Function with Logging
def custom_print(*args, **kwargs):
    message = " ".join(map(str, args))
    timestamped_message = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    
    # Write to log file directly
    with open(log_filename, "a") as log_file:
        log_file.write(timestamped_message + "\n")
    
    # Print to console (optional, controlled by 'to_console' argument)
    if kwargs.get("to_console", True):
        sys.__stdout__.write(timestamped_message + "\n")  # Use original stdout to avoid recursion




# Load Links from File
def load_links():
    with open("links.txt", "r") as file:
        return [line.strip() for line in file if line.strip()]

# Fetch Proxies from Multiple Sources
async def fetch_proxies():
    sources = [
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=1000&country=all&ssl=all&anonymity=elite&simplified=true",
        "https://www.proxy-list.download/api/v1/get?type=http",
    ]
    proxies = set()
    async with aiohttp.ClientSession() as session:
        for source in sources:
            try:
                async with session.get(source, timeout=10) as response:
                    if response.status == 200:
                        text = await response.text()
                        proxies.update(text.strip().split("\n"))
            except Exception as e:
                custom_print(f"Failed to fetch proxies from {source}: {e}")
    return list(proxies)

# Test Proxy Asynchronously
async def test_proxy(proxy):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.google.com", proxy=f"http://{proxy}", timeout=10) as response:
                if response.status == 200:
                    return proxy
    except Exception:
        pass
    return None

# Validate Proxies (Asynchronous)
async def validate_proxies(proxies):
    tasks = [test_proxy(proxy) for proxy in proxies]
    valid_proxies = await asyncio.gather(*tasks)
    valid_proxies = [proxy for proxy in valid_proxies if proxy]
    with open("vproxies.txt", "w") as valid_proxy_file:
        valid_proxy_file.write("\n".join(valid_proxies))
    return valid_proxies

# Proxy Pool Manager
class ProxyPool:
    def __init__(self):
        self.pool = Queue()

    def add_proxies(self, proxies):
        for proxy in proxies:
            self.pool.put(proxy)

    def get_proxy(self):
        if not self.pool.empty():
            return self.pool.get()
        return None

    def size(self):
        return self.pool.qsize()

# Browse with a Proxy
def browse_with_proxy(proxy, links):
    try:
        user_agent = random.choice(USER_AGENTS)
        edge_options = Options()
        edge_options.add_argument(f"user-agent={user_agent}")
        edge_options.add_argument(f"--proxy-server={proxy}")
        edge_options.add_argument("--headless")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--ignore-certificate-errors")

        edge_driver_path = "msedgedriver.exe"
        service = Service(edge_driver_path)

        driver = webdriver.Edge(service=service, options=edge_options)

        for link in links:
            retries = 0
            while retries < 3:  # Retry up to 3 times
                try:
                    driver.set_page_load_timeout(20)  # Set timeout for page load
                    driver.get(link)

                    # Simulate Scrolling
                    for _ in range(5):
                        driver.execute_script("window.scrollBy(0, 500);")
                        time.sleep(random.uniform(1, 3))
                    for _ in range(5):
                        driver.execute_script("window.scrollBy(0, -500);")
                        time.sleep(random.uniform(1, 3))

                    custom_print(f"Visited {link} with Proxy: {proxy}")
                    with open("report.txt", "a") as report_file:
                        report_file.write(f"Visited {link} with Proxy: {proxy}\n")
                    time.sleep(random.uniform(3, 7))
                    break  # Exit retry loop if successful
                except Exception as e:
                    retries += 1
                    custom_print(f"Retrying {link} with Proxy {proxy} ({retries}/3): {e}")
            if retries == 3:
                custom_print(f"Failed to load {link} after 3 retries. Skipping.")
    except Exception as e:
        custom_print(f"Error with Proxy {proxy}: {e}")
    finally:
        driver.quit()  # Always close the browser

# Main Execution Loop
async def main():
    links = load_links()
    custom_print("Fetching proxies...")
    proxies = await fetch_proxies()

    custom_print("Validating proxies...")
    valid_proxies = await validate_proxies(proxies)

    if not valid_proxies:
        custom_print("No valid proxies found. Exiting.")
        return

    custom_print(f"Adding {len(valid_proxies)} valid proxies to the pool.")
    proxy_pool = ProxyPool()
    proxy_pool.add_proxies(valid_proxies)

    while proxy_pool.size() > 0:
        proxy = proxy_pool.get_proxy()
        if proxy:
            custom_print(f"Using Proxy: {proxy}")
            browse_with_proxy(proxy, links)
        else:
            custom_print("No proxies available. Exiting.")
            break

if __name__ == "__main__":
    asyncio.run(main())
