import os
from dotenv import load_dotenv

load_dotenv()

# Load environment variable for environment (default to development)
ENV = os.getenv("ENV", "development").lower()

# Toggle subscription functionality (could be used to turn on/off subscription flows)
ENABLE_SUBSCRIPTIONS = os.getenv("ENABLE_SUBSCRIPTIONS", "true").lower() == "true"

# Stripe configuration: Use test keys and prices in development mode
if ENV == "development":
    STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY_TEST")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY_TEST")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET_CLI") #os.getenv("STRIPE_WEBHOOK_SECRET_TEST")
    STRIPE_PRICE_BASIC = os.getenv("STRIPE_PRICE_BASIC_TEST")
    STRIPE_PRICE_STANDARD = os.getenv("STRIPE_PRICE_STANDARD_TEST")
    STRIPE_PRICE_PREMIUM = os.getenv("STRIPE_PRICE_PREMIUM_TEST")
else:
    STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY_LIVE")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY_LIVE")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET_LIVE")
    STRIPE_PRICE_BASIC = os.getenv("STRIPE_PRICE_BASIC_LIVE")
    STRIPE_PRICE_STANDARD = os.getenv("STRIPE_PRICE_STANDARD_LIVE")
    STRIPE_PRICE_PREMIUM = os.getenv("STRIPE_PRICE_PREMIUM_LIVE")

# Package these settings into a dictionary for easy access
STRIPE_CONFIG = {
    "publishable_key": STRIPE_PUBLIC_KEY,
    "secret_key": STRIPE_SECRET_KEY,
    "webhook_secret": STRIPE_WEBHOOK_SECRET,
    "prices": {
        "basic": STRIPE_PRICE_BASIC,
        "standard": STRIPE_PRICE_STANDARD,
        "premium": STRIPE_PRICE_PREMIUM,
    },
    "webhook_url": os.getenv("STRIPE_WEBHOOK_URL", "http://localhost:8000/app/stripe/webhook")
}

