# subscription.py
import stripe
import os
import logging
from fastapi import FastAPI, HTTPException, Request, Depends, APIRouter
from pydantic import BaseModel
from app.stripe.stripe_config import STRIPE_CONFIG, ENABLE_SUBSCRIPTIONS
from app.auth import verify_token
from app.supabase.profiles import ProfileRepository

stripe.api_key = STRIPE_CONFIG["secret_key"]

# Define your subscription request model
class SubscriptionRequest(BaseModel):
    plan: str  # Expected values: "basic", "standard", "premium"

router = APIRouter()

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
            }
        )
        return {"sessionId": session.id}
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_CONFIG["webhook_secret"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle subscription events
    if event['type'] == 'checkout.session.async_payment_failed':
      session = event['data']['object']
    elif event['type'] == 'checkout.session.async_payment_succeeded':
      session = event['data']['object']
    elif event['type'] == 'checkout.session.completed':
      session = event['data']['object']
    elif event['type'] == 'checkout.session.expired':
      session = event['data']['object']
    else:
      print('Unhandled event type {}'.format(event['type']))

    return {"status": "success"}

async def handle_successful_payment(session):
    repo = ProfileRepository()
    user_id = session["metadata"]["user_id"]
    plan = session["metadata"]["plan"]
    
    repo.update_user_subscription(user_id, plan)
    repo.update_user_credit(user_id, int(session["metadata"]["credits"]))

async def handle_renewal(invoice):
    repo = ProfileRepository()
    subscription = stripe.Subscription.retrieve(invoice["subscription"])
    user_id = subscription["metadata"]["user_id"]
    plan = subscription["metadata"]["plan"]
    
    # Reset credits on successful renewal
    repo.update_user_credit(user_id, PLAN_CONFIG[plan]["credits"])

async def handle_payment_failure(invoice):
    repo = ProfileRepository()
    subscription = stripe.Subscription.retrieve(invoice["subscription"])
    user_id = subscription["metadata"]["user_id"]
    
    # Optionally handle payment failure (e.g., send notification)
    repo.update_user_subscription(user_id, "past_due")
