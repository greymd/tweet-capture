import undetected_chromedriver as uc
# from selenium import webdriver
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import argparse
import base64
import time
from urllib.parse import urlparse

parser = argparse.ArgumentParser(description='Get tweet text and screenshot')
parser.add_argument('url', type=str, help='URL of tweet')
parser.add_argument('--output-text', type=str, help='Output text file')
parser.add_argument('--output-screenshot', type=str, help='Output screenshot file')
args = parser.parse_args()

target_url = args.url
tweet_id = urlparse(target_url).path.rstrip("/").split("/")[-1]
if args.output_text:
    output_text = args.output_text
else:
    output_text = f'{tweet_id}_text.txt'
if args.output_screenshot:
    output_screenshot = args.output_screenshot
else:
    output_screenshot = f'{tweet_id}_screenshot.png'

# Configuration for Chrome Driver
chrome_options = Options()
chrome_options.add_argument("--user-agent=" + "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-setuid-sandbox")
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument('--disable-application-cache')
chrome_options.add_argument('--disable-gpu')
binary_location_candidates = ['/usr/bin/chromium', '/usr/bin/google-chrome', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']
driver_location_candidates = ['/usr/bin/chromedriver', '/usr/local/bin/chromedriver', '/opt/homebrew/bin/chromedriver']
binary_location = None
driver_location = None
for binary in binary_location_candidates:
    if os.path.exists(binary):
        binary_location = binary
        break
for driver in driver_location_candidates:
    if os.path.exists(driver):
        driver_location = driver
        break
driver = uc.Chrome(options=chrome_options, browser_executable_path=binary_location, driver_executable_path=driver_location)
xpath_target_tweet_article = (
    f'(//article[@data-tweet-id="{tweet_id}"]'
    f' | //article[.//a[contains(@href, "/status/{tweet_id}")]])[1]'
)
xpath_legacy_tweet_text = './/*[@data-testid="tweetText"]'
xpath_current_tweet_text = (
    './/div[@dir="auto"'
    ' and contains(concat(" ", normalize-space(@class), " "), " whitespace-pre-wrap ")'
    ' and contains(concat(" ", normalize-space(@class), " "), " text-text ")'
    ' and not(contains(@class, "line-clamp-"))]'
)


def format_tweet_text(main_text, quoted_texts):
    text = main_text
    if quoted_texts:
        quoted_text = "\n\n".join(quoted_texts)
        quoted_text = "\n".join(f"> {line}" if line else ">" for line in quoted_text.splitlines())
        text = f"{main_text}\n\n{quoted_text}"
    return text


def extract_tweet_text(driver, tweet):
    text_elements = tweet.find_elements(by=By.XPATH, value=xpath_legacy_tweet_text)
    if not text_elements:
        text_elements = tweet.find_elements(by=By.XPATH, value=xpath_current_tweet_text)

    texts = [element.text.strip() for element in text_elements if element.text.strip()]
    if texts:
        return format_tweet_text(texts[0], texts[1:])

    description = driver.find_elements(by=By.CSS_SELECTOR, value='meta[property="og:description"]')
    if description:
        return description[0].get_attribute("content").strip()

    return ""

try:
    driver.set_window_size(720, 1200)
    driver.get(target_url)
    tweet = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, xpath_target_tweet_article)))
    text = extract_tweet_text(driver, tweet)
    with open(output_text, 'w') as f:
        f.write(text)
    # take screenshot
    driver.execute_script('arguments[0].scrollIntoView({block: "center", inline: "center"});', tweet)
    driver.execute_script("""
        function hideElement(el) {
            if (!el) {
                return;
            }
            el.style.setProperty('display', 'none', 'important');
            el.style.setProperty('visibility', 'hidden', 'important');
            el.style.setProperty('opacity', '0', 'important');
            el.setAttribute('aria-hidden', 'true');
        }

        for (const bottomBar of document.querySelectorAll('[data-testid="BottomBar"]')) {
            let target = bottomBar;
            while (target.parentElement && target.parentElement.id !== 'layers') {
                const rect = target.getBoundingClientRect();
                if (rect.bottom >= window.innerHeight - 8 && rect.width >= window.innerWidth * 0.5) {
                    target = target.parentElement;
                    continue;
                }
                break;
            }
            hideElement(target);
            hideElement(bottomBar);
        }

        const loginBannerPhrases = [
            "Don’t miss what’s happening",
            "Don't miss what's happening"
        ];
        for (const el of document.querySelectorAll('span')) {
            const text = el.textContent.trim();
            if (!loginBannerPhrases.includes(text)) {
                continue;
            }

            const bottomBar = el.closest('[data-testid="BottomBar"]');
            if (bottomBar) {
                hideElement(bottomBar);
            }

            let target = el.parentElement;
            while (target && target.id !== 'layers') {
                const style = window.getComputedStyle(target);
                const rect = target.getBoundingClientRect();
                if (
                    (style.position === 'fixed' || style.position === 'absolute') &&
                    rect.bottom >= window.innerHeight - 8 &&
                    rect.width >= window.innerWidth * 0.5
                ) {
                    hideElement(target);
                    break;
                }
                target = target.parentElement;
            }
        }

        for (const el of document.querySelectorAll('[data-testid="BottomBar"] span')) {
            if (!loginBannerPhrases.includes(el.textContent.trim())) {
                continue;
            }
            let target = el.closest('[data-testid="BottomBar"]');
            while (target && target.parentElement && target.parentElement.id !== 'layers') {
                const rect = target.parentElement.getBoundingClientRect();
                if (rect.bottom < window.innerHeight - 8 || rect.width < window.innerWidth * 0.5) {
                    break;
                }
                target = target.parentElement;
            }
            if (target) {
                hideElement(target);
                break;
            }
        }

        for (const el of document.querySelectorAll('div')) {
            const style = window.getComputedStyle(el);
            const rect = el.getBoundingClientRect();
            if (
                style.position === 'fixed' &&
                rect.height > 40 &&
                (
                    rect.bottom >= window.innerHeight - 8 ||
                    rect.top <= 8
                )
            ) {
                hideElement(el);
            }
        }
    """)
    time.sleep(1)
    clip = driver.execute_script("""
        const rect = arguments[0].getBoundingClientRect();
        return {
            x: Math.max(0, rect.left + window.scrollX),
            y: Math.max(0, rect.top + window.scrollY),
            width: rect.width,
            height: rect.height,
            scale: 1
        };
    """, tweet)
    if clip["width"] <= 0 or clip["height"] <= 0:
        tweet = driver.find_element(by=By.XPATH, value=xpath_target_tweet_article)
        clip = driver.execute_script("""
            const rect = arguments[0].getBoundingClientRect();
            return {
                x: Math.max(0, rect.left + window.scrollX),
                y: Math.max(0, rect.top + window.scrollY),
                width: rect.width,
                height: rect.height,
                scale: 1
            };
        """, tweet)
    if clip["width"] <= 0 or clip["height"] <= 0:
        raise RuntimeError(f"Invalid tweet screenshot clip: {clip}")
    screenshot = driver.execute_cdp_cmd("Page.captureScreenshot", {
        "format": "png",
        "fromSurface": True,
        "captureBeyondViewport": True,
        "clip": clip,
    })
    with open(output_screenshot, "wb") as f:
        f.write(base64.b64decode(screenshot["data"]))
finally:
    # Close the browser
    driver.quit()
