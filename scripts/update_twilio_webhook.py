import asyncio
import httpx
import os
import sys

# Set Python path to find app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# SSL patch for Windows python 3.13 event loop hang
if sys.platform == "win32":
    import ssl
    import certifi
    _original_create_default_context = ssl.create_default_context
    def patched_create_default_context(purpose=ssl.Purpose.SERVER_AUTH, *, cafile=None, capath=None, cadata=None):
        if cafile is None and capath is None and cadata is None:
            cafile = certifi.where()
        return _original_create_default_context(purpose, cafile=cafile, capath=capath, cadata=cadata)
    ssl.create_default_context = patched_create_default_context

from app.core.config import settings

async def main():
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    public_url = settings.PUBLIC_URL
    
    if not account_sid or not auth_token or not public_url:
        print("Error: Missing TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, or PUBLIC_URL in environment configuration.")
        return
        
    target_webhook = f"{public_url.rstrip('/')}/api/v1/voice/incoming-call"
    print(f"Target Voice Webhook URL: {target_webhook}")
    
    auth = (account_sid, auth_token)
    
    async with httpx.AsyncClient(auth=auth) as client:
        # 1. Fetch incoming phone numbers
        url_numbers = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/IncomingPhoneNumbers.json"
        res = await client.get(url_numbers)
        if res.status_code != 200:
            print(f"Failed to fetch phone numbers: {res.status_code} - {res.text}")
            return
            
        data = res.json()
        numbers = data.get("incoming_phone_numbers", [])
        if not numbers:
            print("No incoming phone numbers found in this Twilio account.")
            return
            
        for num in numbers:
            sid = num.get("sid")
            phone_number = num.get("phone_number")
            current_url = num.get("voice_url")
            print(f"Found number: {phone_number} (SID: {sid}) with Voice URL: {current_url}")
            
            # 2. Update the phone number's VoiceUrl and VoiceMethod
            update_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/IncomingPhoneNumbers/{sid}.json"
            update_data = {
                "VoiceUrl": target_webhook,
                "VoiceMethod": "POST"
            }
            
            res_update = await client.post(update_url, data=update_data)
            if res_update.status_code == 200:
                print(f"Successfully updated phone number {phone_number} to webhook: {target_webhook}")
            else:
                print(f"Failed to update number {phone_number}: {res_update.status_code} - {res_update.text}")

if __name__ == "__main__":
    asyncio.run(main())
