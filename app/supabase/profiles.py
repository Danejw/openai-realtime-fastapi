import os
import logging
from typing import Optional, List
from supabase import create_client, Client
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class Profile(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    image: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    subscription: Optional[str] = None
    credit: Optional[int] = None

class ProfileRepository:
    """
    Repository class responsible for all Supabase CRUD operations
    for the profiles table.
    """
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.table_name = "profiles"

        
    def get_user_email(self, user_id: str) -> Optional[str]:
        """
        Retrieves the email from the profile record in Supabase.
        Returns the email or None if no record is found.
        """
        try:    
            response = self.supabase.table(self.table_name).select("email").eq("id", user_id).execute()
            data = response.data
            if data and len(data) > 0:
                return data[0]["email"]
            else:
                logging.info(f"No profile record found for user_id: {user_id}")
                return None
        except Exception as e:
            logging.error(f"Error fetching email for user_id: {user_id}: {e}")
            return None
        
    def get_user_name(self, user_id: str) -> Optional[str]:
        """
        Retrieves the name from the profile record in Supabase.
        Returns the name or None if no record is found.
        """
        try:
            response = self.supabase.table(self.table_name).select("name").eq("id", user_id).execute()
            data = response.data    
            if data and len(data) > 0:
                return data[0]["name"]
            else:
                logging.info(f"No profile record found for user_id: {user_id}")
                return None
        except Exception as e:
            logging.error(f"Error fetching name for user_id: {user_id}: {e}")
            return None
        
    def get_user_image(self, user_id: str) -> Optional[str]:
        """
        Retrieves the image from the profile record in Supabase.
        Returns the image or None if no record is found.    
        """
        try:
            response = self.supabase.table(self.table_name).select("image").eq("id", user_id).execute()
            data = response.data
            if data and len(data) > 0:
                return data[0]["image"]     
            else:
                logging.info(f"No profile record found for user_id: {user_id}")
                return None
        except Exception as e:
            logging.error(f"Error fetching image for user_id: {user_id}: {e}")
            return None
        
    def update_user_name(self, user_id: str, name: str) -> bool:
        """
        Updates the name of the user in the profile record in Supabase.
        Returns True if update was successful, False otherwise.
        """
        try:
            response = self.supabase.table(self.table_name).update({"name": name}).eq("id", user_id).execute()
            return True
        except Exception as e:
            logging.error(f"Error updating name for user_id: {user_id}: {e}")
            return False
        
    def update_user_image(self, user_id: str, image: str) -> bool:
        """
        Updates the image of the user in the profile record in Supabase.
        Returns True if update was successful, False otherwise.
        """
        try:
            response = self.supabase.table(self.table_name).update({"image": image}).eq("id", user_id).execute()
            return True
        except Exception as e:
            logging.error(f"Error updating image for user_id: {user_id}: {e}")
            return False

    def get_user_subscription(self, user_id: str) -> Optional[str]:
        """
        Retrieves the subscription from the profile record in Supabase.
        Returns the subscription or None if no record is found.
        """
        try:
            response = self.supabase.table(self.table_name).select("subscription").eq("id", user_id).execute()
            data = response.data
            if data and len(data) > 0:
                return data[0]["subscription"]
            else:
                logging.info(f"No profile record found for user_id: {user_id}")
                return None
        except Exception as e:
            logging.error(f"Error fetching subscription for user_id: {user_id}: {e}")
            return None
        
    def update_user_subscription(self, user_id: str, subscription: str) -> bool:
        """
        Updates the subscription of the user in the profile record in Supabase.
        Returns True if update was successful, False otherwise.
        """
        try:
            response = self.supabase.table(self.table_name).update({"subscription": subscription}).eq("id", user_id).execute()
            return True
        except Exception as e:
            logging.error(f"Error updating subscription for user_id: {user_id}: {e}")
            return False
        
    def get_user_credit(self, user_id: str) -> Optional[int]:
        """         
        Retrieves the credit from the profile record in Supabase.
        Returns the credit or None if no record is found.
        """
        try:
            response = self.supabase.table(self.table_name).select("credit").eq("id", user_id).execute()
            data = response.data    
            if data and len(data) > 0:
                return data[0]["credit"]
            else:
                logging.info(f"No profile record found for user_id: {user_id}")
                return None
        except Exception as e:
            logging.error(f"Error fetching credit for user_id: {user_id}: {e}")
            return None
        
    def update_user_credit(self, user_id: str, credit: int) -> bool:
        """
        Updates the credit of the user in the profile record in Supabase.
        Returns True if update was successful, False otherwise.
        """
        try:
            response = self.supabase.table(self.table_name).update({"credit": credit}).eq("id", user_id).execute()
            return True
        except Exception as e:
            logging.error(f"Error updating credit for user_id: {user_id}: {e}")
            return False    
                 

    def get_profile(self, user_id: str) -> Optional[Profile]:
        """
        Retrieves the profile record for a specific user from Supabase.
        Returns a Profile object or None if no record is found.
        """
        try:
            response = self.supabase.table(self.table_name).select("*").eq("id", user_id).execute()
            data = response.data
            if data and len(data) > 0:
                record = data[0]
                return Profile(**record)
            else:
                logging.info(f"No profile record found for user_id: {user_id}")
                return None
        except Exception as e:
            logging.error(f"Error fetching profile data for user {user_id}: {e}")
            return None

