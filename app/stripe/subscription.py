# subscription.py
import json
import stripe
import os
import logging
from fastapi import FastAPI, HTTPException, Request, Depends, APIRouter, Header
from pydantic import BaseModel
from app.stripe.stripe_config import STRIPE_CONFIG, ENABLE_SUBSCRIPTIONS
from app.auth import verify_token
from app.supabase.profiles import ProfileRepository



# Define your subscription request model
class SubscriptionRequest(BaseModel):
    plan: str  # Expected values: "basic", "standard", "premium"

router = APIRouter()

stripe.api_version = '2025-02-24.acacia'

secret_key = STRIPE_CONFIG["secret_key"]
stripe.api_key = secret_key



# Subscription plan configurations
PLAN_CONFIG = {
    "basic": {
        "credits": 2000,
        "token_allowance": 2000000,
        "price_id": STRIPE_CONFIG["prices"]["basic"]
    },
    "standard": {
        "credits": 6000,
        "token_allowance": 6000000,
        "price_id": STRIPE_CONFIG["prices"]["standard"]
    },
    "premium": {
        "credits": 10000,
        "token_allowance": 10000000,
        "price_id": STRIPE_CONFIG["prices"]["premium"]
    }
}

@router.post("/create-checkout-session")
async def create_checkout_session(
    subscription_request: SubscriptionRequest,  # Changed to use request body model
    user=Depends(verify_token)
):
    try:
        plan = subscription_request.plan
        price_id = PLAN_CONFIG[plan]["price_id"]
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=os.getenv("STRIPE_SUCCESS_URL"),
            cancel_url=os.getenv("STRIPE_CANCEL_URL"),
            metadata={
                "user_id": user["id"],
                "plan": plan,
                "credits": PLAN_CONFIG[plan]["credits"]
            },
            subscription_data={
                "metadata": {
                    "user_id": user["id"],
                    "plan": plan,
                    "credits": PLAN_CONFIG[plan]["credits"]
                    }
            }
        )
        return {"sessionId": session.id}
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    webhook_secret = STRIPE_CONFIG["webhook_secret"]

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=webhook_secret
        )
    except ValueError as e:
        logging.error("❌ Invalid payload: %s", e)
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logging.error("❌ Invalid signature: %s", e)
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event.get("type")
    event_data = event.get("data", {}).get("object", {})
    
    

    logging.info("📢 Stripe Event: %s", event_type)
    #logging.info("📦 Event Data: %s", event_data)


    # ✅ Handle successful payment
    if event_type == "invoice.paid":
        lines = event_data.get("lines", {}).get("data", [])
        if lines and "metadata" in lines[0]:
            metadata = lines[0]["metadata"]
            user_id = metadata.get("user_id")    
            plan = metadata.get("plan")
            credits = metadata.get("credits")

        if not user_id or not plan or not credits:
            logging.warning("⚠️ Missing metadata. Cannot update user subscription.")
        else:
            try:
                credits = int(credits)
                logging.info(f"🎯 Updating user {user_id}: Plan={plan}, Credits={credits}")

                repo = ProfileRepository()
                updated_sub = repo.update_user_subscription(user_id, plan)
                updated_credits = repo.update_user_credit(user_id, credits)

                logging.info("✅ Supabase update response:", "updated_sub:", updated_sub, "updated_credits:", updated_credits)
            except Exception as e:
                logging.error(f"❌ Failed to update Supabase: {e}")

    elif event_type == "invoice.payment_failed":
        logging.warning("💳 Payment failed. Consider notifying the user.")

    elif event_type == "checkout.session.completed":
        logging.info("✅ Checkout session completed")
        
    return {"status": "success"}


@router.get("/stripe/config")
async def get_stripe_config():
    return {"publishableKey": STRIPE_CONFIG["publishable_key"]}

