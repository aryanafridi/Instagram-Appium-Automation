from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
import time
import subprocess
import os
import sys
import platform
import random
import base64
from appium.options.android import UiAutomator2Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.common.exceptions import NoSuchAttributeException, StaleElementReferenceException, \
    NoSuchElementException, TimeoutException, ElementClickInterceptedException, WebDriverException, \
    ElementNotInteractableException

""" Run Appium server before running """
# Setting current directory
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(os.path.abspath(sys.executable)))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Constants
COMMON_EXCEPTIONS = (NoSuchElementException, TimeoutException,
                     StaleElementReferenceException, ElementClickInterceptedException,
                     WebDriverException, ElementNotInteractableException,
                     NoSuchAttributeException)
CLEAR = "cls" if platform.system().upper() == "WINDOWS" else "clear"
DEVICE_UPLOAD_PATH = "/sdcard/Download/ig"

def exceptional_handler(func):
    """ Exception handler wrapper to retry the function until max retries reached"""
    def wrapper(*args, **kwargs):
        retry = kwargs.get("retry", 0)
        err_callback = kwargs.get("err_callback", None)
        max_retries = kwargs.get("max_retries", 2)
        if retry >= max_retries:
            if err_callback is not None:
                err_callback(*args, **kwargs)
            else:
                raise Exception("Maximum retries reached!")
        try:
            if "retry" in list(kwargs.keys()):
                kwargs.pop("retry")
            if "max_retries" in list(kwargs.keys()):
                kwargs.pop("max_retries")
            if "err_callback" in list(kwargs.keys()):
                kwargs.pop("err_callback")
            return func(*args, **kwargs)
        except COMMON_EXCEPTIONS:
            time.sleep(5)
            return wrapper(retry=retry + 1, max_retries=max_retries, *args, **kwargs)
    return wrapper


def wait_until(condition_func):
    """ Wrapper to wait until certain conditions met."""
    def wrapper(*args, **kwargs):
        kwargs.get("before_loop", lambda: True)()
        max_attempts = kwargs.get("max_tries", -1)
        dots = 1
        attempt = 0
        not_completed = False
        while True:
            kwargs.get("in_loop_before", lambda: True)()
            if condition_func(*args):
                break
            if max_attempts != -1 and attempt >= max_attempts:
                not_completed = True
                break
            attempt += 1
            print(f"{kwargs.get('message', 'Waiting')}{'.' * dots}", end="\r")
            dots = 1 if dots > 2 else dots + 1
            kwargs.get("in_loop_after", lambda: True)()
            time.sleep(kwargs.get("sleep", 0.5))
            print(" " * 100, end="\r")
        kwargs.get("after_loop", lambda: True)()
        return not not_completed
    return wrapper



def generate_random_comment():
    """ Random comments generation"""
    adjectives = ["amazing", "beautiful", "stunning", "awesome", "fantastic", "gorgeous", "incredible", "lovely", "cool", "breathtaking"]
    nouns = ["post", "photo", "pic", "shot", "image", "view", "scene", "moment", "capture", "composition"]
    emojis = ["😍", "🌟", "💕", "🌈", "🌼", "📸", "🙌", "👏", "❤️", "🌞"]
    phrases = [
        "Love this!", "Wow, just wow!", "So inspiring!", "This is perfect!", "Totally agree!", 
        "Absolutely stunning!", "Can I save this?", "Goals!", "Speechless!", "This made my day!"
    ]
    structure = random.choice([1, 2, 3]) 
    if structure == 1:
        comment = f"{random.choice(adjectives).capitalize()} {random.choice(nouns)} {random.choice(emojis)}"
    elif structure == 2:
        comment = f"{random.choice(phrases)} {random.choice(emojis)}"
    else:
        comment = f"{random.choice(emojis)} {random.choice(adjectives)} and {random.choice(adjectives)} {random.choice(nouns)}!"
    return comment

def check_installed_app(phone_serial, package_name="com.instagram.android"):
    """ Check if app is installed or not on device """
    command = ["adb", "-s", phone_serial, "shell", "pm", "list", "packages", package_name]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if f"package:{package_name}" in result.stdout:
        print(f"{package_name} is already installed on {phone_serial}.")
        return True
    else:
        print(f"{package_name} is NOT installed on {phone_serial}.")
        return False

def install_apk(phone_serial, apk_path=os.path.abspath("instagram.apk")):
    """ Apk file installation """
    if not os.path.exists(apk_path):
        print(f"APK file not found at {apk_path}.")
        return
    
    print(f"Installing Instagram APK on {phone_serial}...")
    command = ["adb", "-s", phone_serial, "install", "-r", apk_path]
    subprocess.run(command, check=True)
    print(f"Instagram APK installed successfully on {phone_serial}.")

class InstagramDMAutomation:
    """ DM Automation class containing all dm automation """
    def __init__(self, platform_version, phone_serial, full_reset=False):
        self.phone_serial = phone_serial
        self.platform_version = platform_version
        self.driver = None
        self.full_reset = full_reset

    def connect_appium(self):
        """ Connect appium """
        # permissions = self.get_permissions(self.phone_serial)
        # if not permissions:
        #     print("No permissions found or invalid package name.")
        # else:
        #     self.grant_permissions(permissions, self.phone_serial)
        self.close_app()
        desired_caps = {
            "platformName": "Android",
            "deviceName": self.phone_serial,
            "platformVersion": self.platform_version,
            "udid": self.phone_serial,
            "appPackage": "com.instagram.android",
            "appActivity": "com.instagram.mainactivity.LauncherActivity",
            "automationName": "UiAutomator2",
            "noReset": True,
            # "fullReset": self.full_reset,
            "forceAppLaunch": True,
            "shouldTerminateApp": True
        }
        self.driver = self.setup_driver(desired_caps)
        time.sleep(5)
        self.driver.activate_app("com.instagram.android")
    
    def setup_driver(self, desired_caps):
        """ Setup Drivers """
        capabilities_options = UiAutomator2Options().load_capabilities(desired_caps)
        driver = webdriver.Remote(f"http://127.0.0.1:4723", options=capabilities_options)
        return driver
    
    def run_adb_command(self, command):
        
        try:
            result = subprocess.check_output(command, shell=True, text=True)
            return result.strip()
        except subprocess.CalledProcessError as e:
            return ""

    def get_permissions(self, device_name):
        print(f"Fetching permissions for package: com.instagram.android")
        command = f"adb -s {device_name} shell dumpsys package com.instagram.android"
        output = self.run_adb_command(command)
        permissions = []
        
        for line in output.splitlines():
            if "permission" in line.lower():
                permissions.append(line.strip())
        return permissions

    def grant_permissions(self, permissions, device_name):
        print("Granting permissions!")
        for permission in permissions:
            if "permission." in permission:
                permission_name = permission.split(":")[-1].strip()
                command = f"adb -s {device_name} shell pm grant com.instagram.android {permission_name}"
                self.run_adb_command(command)

    @exceptional_handler
    def tap_element(self, by, value):
        element = self.driver.find_element(by=by, value=value)
        time.sleep(1)
        element.click()

    @exceptional_handler
    def write(self, by, value, text, clear=True):
        element = self.driver.find_element(by=by, value=value)
        if clear:
            element.clear()
        element.send_keys(text)

    def login(self, username, password):
        """Log in to Instagram."""
        wait_until(lambda: self.driver.find_elements(by=AppiumBy.ACCESSIBILITY_ID, value="Username, email or mobile number") or \
                   self.driver.find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().resourceId("com.instagram.android:id/action_bar_inbox_button")'))(
                       message="Waiting until login form loads")
        if self.driver.find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().resourceId("com.instagram.android:id/action_bar_inbox_button")'):
            require_sign_in = self.change_profile(username)
            if not require_sign_in:
                self.go_to_top()
                return
        self.tap_element(AppiumBy.ACCESSIBILITY_ID, "Username, email or mobile number")
        self.write(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(0)', username)
        self.tap_element(AppiumBy.ACCESSIBILITY_ID, "Password")
        self.write(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(1)', password)
        self.driver.hide_keyboard()
        self.tap_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Log in")')
        
        wait_until(
            lambda: self.driver.find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().description("Save")') or \
                self.driver.find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().resourceId("com.instagram.android:id/action_bar_inbox_button")'))(
                    message="Waiting until signed in"
                )
        time.sleep(5)
        if self.driver.find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().description("Save")'):
            self.tap_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Save")')
        wait_until(lambda: self.driver.find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().resourceId("com.instagram.android:id/action_bar_inbox_button")'))(message="Waiting until homepage shows")
    
    def change_profile(self, username):
        """ Change profile on IG application """
        self.tap_element(AppiumBy.ACCESSIBILITY_ID, "Profile")
        wait_until(lambda: self.driver.find_elements(by=AppiumBy.ID, value="com.instagram.android:id/action_bar_large_title_auto_size"))(message="Waiting until profile shows")
        current_prof = self.driver.find_element(AppiumBy.ID, "com.instagram.android:id/action_bar_large_title_auto_size")
        if current_prof.text == username:
            return False
        current_prof.click()
        if self.driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{username}")'):
            self.tap_element(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{username}")')
            return False
        self.tap_element(AppiumBy.ACCESSIBILITY_ID, "Add Instagram account")
        self.tap_element(AppiumBy.ACCESSIBILITY_ID, "Log into existing account")
        time.sleep(4)
        if self.driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Log into another account")'):
            self.tap_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Log into another account")')
        return True

    def scroll_randomly(self):
        """ Randomly Scroll """
        for _ in range(4):
            actions = ActionChains(self.driver)
            actions.w3c_actions = ActionBuilder(self.driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
            x_axis = random.randint(100, 800)
            actions.w3c_actions.pointer_action.move_to_location(x_axis, random.randint(1200, 1600))
            actions.w3c_actions.pointer_action.pointer_down()
            actions.w3c_actions.pointer_action.move_to_location(x_axis + random.randint(-40, 40), random.randint(400, 1000))
            actions.w3c_actions.pointer_action.release()
            actions.perform()

    def like(self):
        """ Perform Like Action """
        wait_until(lambda: self.driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "Liked") or self.driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "Like"))(message="Waiting until like button shows")
        if self.driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "Liked"):
            return
        self.tap_element(AppiumBy.ACCESSIBILITY_ID, "Like")
    
    def comment(self, comment_text):
        """ Perform Like Action """
        self.tap_element(AppiumBy.ACCESSIBILITY_ID, "Comment")
        self.tap_element(AppiumBy.ID, "com.instagram.android:id/layout_comment_thread_edittext")
        self.write(AppiumBy.ID, "com.instagram.android:id/layout_comment_thread_edittext", comment_text)
        self.tap_element(AppiumBy.ACCESSIBILITY_ID, "Post")
        
        wait_until(lambda: (self.driver.find_elements(by=AppiumBy.ID, value="com.instagram.android:id/feed_tab")) and (not self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/layout_comment_thread_edittext")))(
            message="Waiting until homepage", in_loop_before=lambda: self.driver.execute_script('mobile: pressKey', {"keycode": 4}))

    def warmup(self, comment=False):
        """ Perform Warmup Action """
        for _ in range(random.randint(2, 20)):
            self.scroll_randomly()
            time.sleep(random.uniform(1, 10))
            if (random.choice([True, *[False] * 5])) and (self.driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "Like")):
                self.like()
            if (comment) and (random.choice([True, *[False] * 15])) and (self.driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "Comment")):
                self.comment(generate_random_comment())
        if (random.choice([True, False, False])):
            self.go_to_top()
        # self.driver.find_element("android=new UiScrollable(new UiSelector().scrollable(true)).flingToBeginning(100)")
    
    def go_to_top(self):
        """ Go to top """
        self.tap_element(AppiumBy.ID, 'com.instagram.android:id/feed_tab')
        time.sleep(2)
    
    def open_post(self, link):
        """ Open a post """
        subprocess.run(["adb", "-s", self.phone_serial, "shell", "am", "start",
            "-a", "android.intent.action.VIEW", 
            "-d", f'instagram://media?id={link.split("?")[0].strip("/").split("/")[-1]}'],
            check=True
        )
        time.sleep(2)

    def post(self, text, media, username):
        """ Post image on Instagram """
        subprocess.run(
            ["adb", "-s", self.phone_serial, "shell", f"rm -rf {DEVICE_UPLOAD_PATH}/*"],
            check=True
        )
        filename = os.path.basename(media)
        with open(media, "rb") as file:
            file_content = file.read()
            encoded_file = base64.b64encode(file_content).decode("utf-8")

        self.driver.push_file(f"{DEVICE_UPLOAD_PATH}/{filename}", encoded_file)
        time.sleep(4)
        self.tap_element(AppiumBy.ID, "com.instagram.android:id/creation_tab")
        self.tap_element(AppiumBy.ACCESSIBILITY_ID, "Story Settings")
        self.tap_element(AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Next\")")
        time.sleep(3)
        if self.driver.find_elements(by=AppiumBy.ACCESSIBILITY_ID, value="OK"):
            self.tap_element(AppiumBy.ACCESSIBILITY_ID, "OK")
        time.sleep(3)
        caption_id = "com.instagram.android:id/caption_text_view"
        if self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/caption_input_text_view"):
            caption_id = "com.instagram.android:id/caption_input_text_view"
        self.tap_element(AppiumBy.ID, caption_id)
        self.write(AppiumBy.ID, caption_id, text)
        time.sleep(2)
        self.driver.execute_script('mobile: pressKey', {"keycode": 4})
        time.sleep(2)
        self.tap_element(AppiumBy.ID, "com.instagram.android:id/share_footer_button")
        time.sleep(4)
        try:
            if self.driver.find_elements(by=AppiumBy.ID, value="com.instagram.android:id/dismiss_button"):
                self.tap_element(AppiumBy.ID, "com.instagram.android:id/dismiss_button")
        except:
            pass
        wait_until(lambda: self.driver.find_elements(by=AppiumBy.ACCESSIBILITY_ID, value=f"Profile picture of {username}") or \
                   self.driver.find_elements(by=AppiumBy.ACCESSIBILITY_ID, value=f"Go to {username}'s profile"))(message="Waiting until uploaded")

    def close_app(self):
        """ Close the app """
        try:
            command = ["adb", "-s", self.phone_serial, "shell", "am", "force-stop", "com.instagram.android"]
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to close app: {e}")

    def share(self, usernames):
        """ Perform share function on post"""
        self.tap_element(AppiumBy.ACCESSIBILITY_ID, "Send post")
        for username in usernames.split(","):
            if not self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/search_edit_text"):
                self.tap_element(AppiumBy.ID, "com.instagram.android:id/search_row")
            self.write(AppiumBy.ID, "com.instagram.android:id/search_edit_text", username.strip())
            time.sleep(2)
            wait_until(lambda: not self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/search_loading_spinner"))(message="Waiting until search completes")
            time.sleep(2)

            if not self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/user_row_background"):
                if self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/one_tap_send_button_spinning_gradient_border"):
                    self.tap_element(AppiumBy.ID, "com.instagram.android:id/one_tap_send_button_spinning_gradient_border")
                    time.sleep(4)
                continue
            self.tap_element(AppiumBy.ID, "com.instagram.android:id/user_row_background")
        time.sleep(3)
        if self.driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "Done"):
            self.tap_element(AppiumBy.ACCESSIBILITY_ID, "Done")
        else:
            wait_until(lambda: (self.driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "Send")) or (self.driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "Send separately")))(
                message="Waiting until send button shows", in_loop_after=lambda: self.driver.execute_script('mobile: pressKey', {"keycode": 4}), sleep=3, max_tries=5)
            if self.driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "Send separately"):
                self.tap_element(AppiumBy.ACCESSIBILITY_ID, "Send separately")
            else:
                self.tap_element(AppiumBy.ACCESSIBILITY_ID, "Send")
        time.sleep(3)
    
    def go_to_dm(self, username):
        """ Go to specific DM """
        self.tap_element(AppiumBy.ID, "com.instagram.android:id/action_bar_inbox_button")
        self.tap_element(AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.TextView\").instance(0)")
        self.write(AppiumBy.ID, "com.instagram.android:id/search_bar_real_field", username)
        wait_until(lambda: not self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/search_loading_spinner"))(message="Waiting until search completes")
        self.tap_element(AppiumBy.ID, "com.instagram.android:id/row_inbox_container")
        

    def send_dm(self, dm_username, message):
        """ Send the DM """
        if not self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/row_thread_composer_edittext"):
            self.go_to_dm(dm_username)
        
        wait_until(lambda: self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/row_thread_composer_edittext") or \
                   self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/bb_primary_action_container") or \
                    self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/disabled_composer_text_container"))(message="Waiting until loaded")
        if self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/bb_primary_action_container"):
            self.tap_element(AppiumBy.ID, "com.instagram.android:id/bb_primary_action_container")
        wait_until(lambda: self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/row_thread_composer_edittext")  or \
                    self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/disabled_composer_text_container"))(message="Waiting until loaded")
        if self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/disabled_composer_text_container"):
            return
        self.tap_element(AppiumBy.ID, "com.instagram.android:id/row_thread_composer_edittext")
        self.write(AppiumBy.ID, "com.instagram.android:id/row_thread_composer_edittext", message)
        time.sleep(2)
        if self.driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "Send"):
            self.tap_element(AppiumBy.ACCESSIBILITY_ID, "Send")
        else:
            self.tap_element(AppiumBy.ID, "com.instagram.android:id/row_thread_composer_button_send")
        # all_messages = self.driver.find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().resourceId("com.instagram.android:id/message_content_horizontal_placeholder_container")')
        wait_until(lambda: self.driver.find_elements(AppiumBy.ACCESSIBILITY_ID, message))(message="Waiting until sent")
        time.sleep(3)


    def check_replies(self, username):
        """ Check for replies """
        self.go_to_dm(username)
        time.sleep(3)
        wait_until(lambda: self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/row_thread_composer_edittext") or \
                   self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/bb_primary_action_container") or \
                    self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/disabled_composer_text_container"))(message="Waiting until loaded")
        if self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/bb_primary_action_container"):
            self.tap_element(AppiumBy.ID, "com.instagram.android:id/bb_primary_action_container")
        wait_until(lambda: self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/row_thread_composer_edittext")  or \
                    self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/disabled_composer_text_container"))(message="Waiting until loaded")
        if self.driver.find_elements(AppiumBy.ID, "com.instagram.android:id/disabled_composer_text_container"):
            return ""
        all_messages = self.driver.find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().resourceId("com.instagram.android:id/message_content_horizontal_placeholder_container")')
        history = []
        
        for message in all_messages:
            if not message.find_elements(AppiumBy.ACCESSIBILITY_ID, "Profile picture"):
                history.append(
                    {"role": "assistant", "content": message.find_element(AppiumBy.XPATH, "//android.widget.TextView").text}
                )
                continue
            history.append(
                {"role": "user", "content": message.find_element(AppiumBy.XPATH, "//android.widget.TextView").text}
            )
        return history


    def close_appium(self):
        """ Close appium driver """
        if self.driver is not None:
            self.driver.quit()
            self.close_app()
