#!/usr/bin/env python3
"""
SpinPK Auto Spin Bot
Runs every hour via GitHub Actions
"""

import requests
import json
import time
import os
import sys
from datetime import datetime
import logging

# ==================== CONFIGURATION ====================
# GitHub Secrets se read karein
TOKEN = os.environ.get('SPINPK_TOKEN', '1f5587940e9546229e1c1426cea08f9a88e89a48db6f018d04420a5e0e6e04db')
DEVICE_ID = os.environ.get('SPINPK_DEVICE_ID', 'f607b24295e557fe')

# API Endpoints
BASE_URL = "https://spinpk.net/api"
HEARTBEAT_URL = f"{BASE_URL}/me.php"
SPIN_URL = f"{BASE_URL}/spin.php"

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('spinpk_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==================== HEADERS ====================
def get_headers():
    """Return headers for API requests"""
    return {
        'sec-ch-ua-platform': '"Android"',
        'authorization': f'Bearer {TOKEN}',
        'x-device-id': DEVICE_ID,
        'user-agent': 'Mozilla/5.0 (Linux; Android 11; Infinix X659B Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/152.0.7977.30 Mobile Safari/537.36',
        'sec-ch-ua': '"Chromium";v="152", "Not?A_Brand";v="24", "Android WebView";v="152"',
        'content-type': 'application/json',
        'sec-ch-ua-mobile': '?1',
        'accept': '/',
        'origin': 'null',
        'x-requested-with': 'com.spinpk.app',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'accept-encoding': 'gzip, deflate, zstd',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=1, i'
    }

# ==================== API FUNCTIONS ====================
def heartbeat():
    """Send heartbeat request to /me.php"""
    try:
        logger.info("📤 Sending heartbeat...")
        headers = get_headers()
        data = {"action": "heartbeat"}
        
        response = requests.post(
            HEARTBEAT_URL,
            headers=headers,
            json=data,
            timeout=30
        )
        
        logger.info(f"📥 Heartbeat response: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                logger.info(f"✅ Heartbeat successful: {json.dumps(result, indent=2)[:200]}...")
                
                # Save heartbeat result
                with open('heartbeat_result.json', 'w') as f:
                    json.dump(result, f, indent=2)
                
                return result
            except json.JSONDecodeError:
                logger.error(f"❌ Failed to parse heartbeat response: {response.text[:200]}")
                return None
        else:
            logger.error(f"❌ Heartbeat failed: {response.status_code} - {response.text[:200]}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Heartbeat exception: {str(e)}")
        return None

def spin():
    """Send spin request to /spin.php"""
    try:
        logger.info("🎰 Sending spin request...")
        headers = get_headers()
        data = {"action": "play"}
        
        response = requests.post(
            SPIN_URL,
            headers=headers,
            json=data,
            timeout=30
        )
        
        logger.info(f"📥 Spin response: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                logger.info(f"✅ Spin successful: {json.dumps(result, indent=2)[:200]}...")
                
                # Extract reward information if available
                if 'data' in result:
                    if 'coins' in result['data']:
                        logger.info(f"🪙 Coins: {result['data'].get('coins', 'N/A')}")
                    if 'prize' in result['data']:
                        logger.info(f"🏆 Prize: {result['data'].get('prize', 'N/A')}")
                
                # Save spin result
                with open('spin_result.json', 'w') as f:
                    json.dump(result, f, indent=2)
                
                return result
            except json.JSONDecodeError:
                logger.error(f"❌ Failed to parse spin response: {response.text[:200]}")
                return None
        else:
            logger.error(f"❌ Spin failed: {response.status_code} - {response.text[:200]}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Spin exception: {str(e)}")
        return None

def check_token_validity():
    """Check if token is valid by making a test request"""
    try:
        logger.info("🔍 Checking token validity...")
        headers = get_headers()
        data = {"action": "heartbeat"}
        
        response = requests.post(
            HEARTBEAT_URL,
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("✅ Token is valid")
            return True
        elif response.status_code == 401:
            logger.error("❌ Token is invalid or expired")
            return False
        else:
            logger.warning(f"⚠️ Token check returned: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Token check failed: {str(e)}")
        return False

# ==================== MAIN FUNCTION ====================
def run_bot():
    """Main bot execution function"""
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(f"🚀 SpinPK Bot Started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Check token validity
    if not check_token_validity():
        logger.error("❌ Token invalid! Exiting...")
        return False
    
    # Step 1: Send heartbeat
    logger.info("\n📌 STEP 1: Heartbeat")
    heartbeat_result = heartbeat()
    if not heartbeat_result:
        logger.warning("⚠️ Heartbeat failed, but continuing...")
    
    # Step 2: Send spin request
    logger.info("\n📌 STEP 2: Spin")
    spin_result = spin()
    if not spin_result:
        logger.warning("⚠️ Spin failed!")
    
    # Save summary
    summary = {
        'timestamp': start_time.isoformat(),
        'heartbeat_success': heartbeat_result is not None,
        'spin_success': spin_result is not None,
        'heartbeat_response': heartbeat_result,
        'spin_response': spin_result
    }
    
    with open('summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Log completion
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info("\n" + "=" * 60)
    logger.info(f"✅ Bot completed in {duration:.2f} seconds")
    logger.info("=" * 60)
    
    return spin_result is not None

# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    # Run the bot
    success = run_bot()
    
    # Exit with appropriate code for GitHub Actions
    if success:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure
