import logging
import traceback
from telegram import Update, Bot
from telegram.ext import CommandHandler, Application, CallbackContext
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Telegram bot token
TELEGRAM_BOT_TOKEN = '7312234490:AAGxD8VOVAex8a_xqpQJ9N8sFzR-6T2_Tm8'

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Fixed password
NEW_PASSWORD = "NewPass123!"

# Function to automate Netflix password change
def change_netflix_password(email, old_password, chat_id, bot):
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")  # Uncomment to run headless
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://www.netflix.com/login")

        # Log in to Netflix
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "userLoginId"))
        ).send_keys(email)
        driver.find_element(By.NAME, "password").send_keys(old_password)

        # Wait for the login button to be clickable and click it
        login_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign In')]"))
        )
        login_button.click()

        # Wait for login to complete and navigate to the account settings
        WebDriverWait(driver, 30).until(
            EC.url_contains("https://www.netflix.com/browse")
        )
        driver.get("https://www.netflix.com/account")

        # Navigate to password change page
        driver.get("https://www.netflix.com/password")

        # Wait for the password change form to be present
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "currentPassword"))
        )

        # Change password
        driver.find_element(By.NAME, "currentPassword").send_keys(old_password)
        driver.find_element(By.NAME, "newPassword").send_keys(NEW_PASSWORD)
        driver.find_element(By.NAME, "confirmNewPassword").send_keys(NEW_PASSWORD)

        # Wait for the change password button to be clickable and click it
        change_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save')]"))
        )
        change_button.click()

        # Check if navigated to confirmation page
        try:
            WebDriverWait(driver, 30).until(
                EC.url_contains("https://www.netflix.com/account?confirm=password")
            )
            logger.info("Password changed successfully. Sending new password to user.")
            bot.send_message(chat_id=chat_id, text=f"Password changed successfully!\nNew Password: {NEW_PASSWORD}")
            return NEW_PASSWORD
        except TimeoutException:
            # Check if an error message indicates incorrect current password
            error_message_elements = WebDriverWait(driver, 30).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "error-message"))
            )
            for element in error_message_elements:
                if "Incorrect password" in element.text:
                    logger.error("Incorrect password for account email.")
                    bot.send_message(chat_id=chat_id, text="Incorrect current password. Please verify and try again.")
                    return "Incorrect current password. Please verify and try again."

    except Exception as e:
        logger.error(f"Error interacting with Netflix: {e}")
        logger.error(traceback.format_exc())
        bot.send_message(chat_id=chat_id, text="An error occurred while changing the password.")
        return None

    finally:
        driver.quit()

# Command handler for /setnetflix command
async def set_netflix_credentials(update: Update, context: CallbackContext):
    message = update.message.text
    if len(message.split()) != 3:
        await update.message.reply_text("Usage: /setnetflix <email> <password>")
        return

    _, email, old_password = message.split()
    chat_id = update.message.chat_id
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    try:
        new_password = change_netflix_password(email, old_password, chat_id, bot)
        if new_password and "Incorrect current password" not in new_password:
            response = f"Password changed successfully!\nNew Password: {new_password}"
        else:
            response = "Failed to change password."
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        await update.message.reply_text("An error occurred while processing your request.")

def main() -> None:
    # Create the Application instance
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("setnetflix", set_netflix_credentials))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
