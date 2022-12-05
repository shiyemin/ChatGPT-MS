"""Make some requests to OpenAI's chatbot"""

from playwright.sync_api import sync_playwright

if __name__ == "__main__":
    headless = False
else:
    headless = True

PLAY = sync_playwright().start()
BROWSER = PLAY.chromium.launch_persistent_context(
    user_data_dir="/tmp/playwright",
    headless=headless,
)
PAGE = BROWSER.new_page()

def get_input_box():
    """Get the child textarea of `PromptTextarea__TextareaWrapper`"""
    return PAGE.query_selector("textarea")

def is_logged_in():
    # See if we have a textarea with data-id="root"
    return get_input_box() is not None

def get_token():
    PAGE.goto("https://chat.openai.com/")
    if not is_logged_in():
        print("Please make sure change headless to False and log in to OpenAI Chat on your browser")
        print("Press enter when you're done")
        input()
        return None
    else:
        cookies = BROWSER.cookies()
        found = False
        for c in cookies:
            if c["name"] == "__Secure-next-auth.session-token":
                token = c["value"]
                found = True
                break
        if not found:
            print("not found")
            return None
        config = {
            "Authorization": "<API_KEY>",
            "session_token": token,
        }
        return config

if __name__ == "__main__":
    PAGE.goto("https://chat.openai.com/")
    print("Please make sure change headless to False and log in to OpenAI Chat on your browser")
    print("Press enter when you're done")
    input()
