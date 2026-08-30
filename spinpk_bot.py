import requests
import os
import json
import logging
from datetime import datetime, timedelta
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SpinPKBot:
    def __init__(self):
        self.token = os.getenv('SPINPK_TOKEN')
        self.device_id = os.getenv('SPINPK_DEVICE_ID', 'f607b24295e557fe')
        self.base_url = 'https://spinpk.net/api'
        self.user_data = None
        self.config = None
        self.session = requests.Session()
        
        # Enhanced Validation with detailed error messages
        logger.info("=" * 60)
        logger.info("🔐 Validating Configuration...")
        logger.info("=" * 60)
        
        if not self.token:
            logger.error("❌ SPINPK_TOKEN is NOT set!")
            logger.error("📝 Action Required: Add SPINPK_TOKEN to GitHub Secrets")
            logger.error("📍 Go to: Repository Settings → Secrets and variables → Actions")
            raise ValueError("Missing SPINPK_TOKEN secret")
        
        if len(self.token.strip()) == 0:
            logger.error("❌ SPINPK_TOKEN is empty!")
            raise ValueError("SPINPK_TOKEN cannot be empty")
        
        logger.info(f"✅ SPINPK_TOKEN found (length: {len(self.token)} chars)")
        logger.info(f"✅ SPINPK_DEVICE_ID: {self.device_id[:8]}...{self.device_id[-4:] if len(self.device_id) > 12 else ''}")
        logger.info("=" * 60)
        
    def get_headers(self):
        """Generate headers for API requests"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Infinix X659B Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/152.0.7977.42 Mobile Safari/537.36',
            'Content-Type': 'application/json',
            'X-Device-Id': self.device_id,
            'X-Requested-With': 'com.spinpk.app',
            'Authorization': f'Bearer {self.token}',
            'Accept': '*/*',
            'Origin': 'null'
        }
        
        return headers
    
    def get_user_data(self):
        """Get user info and config"""
        logger.info("📊 Fetching user data...")
        
        try:
            url = f'{self.base_url}/auth.php'
            
            payload = {"action": "me"}
            
            logger.info(f"🔗 Calling: {url}")
            logger.info(f"📤 Headers: Authorization: Bearer {self.token[:10]}...")
            
            response = self.session.post(
                url,
                headers=self.get_headers(),
                json=payload,
                timeout=10
            )
            
            logger.info(f"📥 Response Status: {response.status_code}")
            
            # Better error handling for auth failures
            if response.status_code == 401:
                logger.error("❌ 401 Unauthorized - Token is invalid or expired")
                logger.error("📝 Possible Solutions:")
                logger.error("   1. Token may have expired - refresh it from SpinPK app")
                logger.error("   2. Device ID mismatch - verify SPINPK_DEVICE_ID")
                logger.error("   3. Token format incorrect - check for extra spaces/characters")
                logger.error("📝 Update your secrets in GitHub: Settings → Secrets and variables → Actions")
                return False
            
            if response.status_code != 200:
                logger.error(f"❌ API Error {response.status_code}: {response.text}")
                return False
            
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('ok'):
                self.user_data = data.get('user', {})
                self.config = data.get('config', {})
                
                logger.info(f"✅ User: {self.user_data.get('name', 'Unknown')}")
                logger.info(f"💰 Balance: {self.user_data.get('balance')} PKR")
                logger.info(f"🎡 Last spin: {datetime.fromtimestamp(self.user_data.get('last_spin_at', 0))}")
                
                return True
            else:
                error = data.get('error', data.get('message', 'Unknown error'))
                logger.error(f"❌ Failed to get user data: {error}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("❌ Request timeout - API server not responding")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("❌ Connection error - check internet connection")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request failed: {e}")
            logger.error(f"📝 Response content: {e.response.text if hasattr(e, 'response') and e.response else 'N/A'}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON response: {e}")
            return False
    
    def calculate_next_spin_time(self):
        """Calculate when next spin will be available"""
        if not self.user_data or not self.config:
            return None
        
        last_spin = self.user_data.get('last_spin_at', 0)
        spin_interval = self.config.get('spin_interval_sec', 7800)  # Default 2h 10m (7800 seconds)
        
        next_spin_time = last_spin + spin_interval
        return next_spin_time
    
    def can_spin(self):
        """Check if user can spin"""
        if not self.user_data:
            return False
        
        last_spin = self.user_data.get('last_spin_at', 0)
        spin_interval = self.config.get('spin_interval_sec', 7800)
        current_time = int(time.time())
        
        time_since_spin = current_time - last_spin
        
        hours = spin_interval // 3600
        minutes = (spin_interval % 3600) // 60
        seconds = spin_interval % 60
        
        logger.info(f"⏱️  Last spin: {datetime.fromtimestamp(last_spin)}")
        logger.info(f"⏱️  Spin interval: {spin_interval}s ({hours}h {minutes}m {seconds}s)")
        logger.info(f"⏱️  Time since last spin: {time_since_spin}s")
        
        if time_since_spin >= spin_interval:
            logger.info(f"✅ Can spin! ({time_since_spin}s >= {spin_interval}s)")
            return True
        else:
            wait_time = spin_interval - time_since_spin
            h = wait_time // 3600
            m = (wait_time % 3600) // 60
            s = wait_time % 60
            logger.warning(f"⏳ Cannot spin yet. Wait {h}h {m}m {s}s")
            return False
    
    def spin(self):
        """Perform spin action"""
        logger.info("🎡 Attempting to spin...")
        
        try:
            url = f'{self.base_url}/spin.php'
            
            payload = {"action": "spin"}
            
            response = self.session.post(
                url,
                headers=self.get_headers(),
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('ok'):
                win_amount = data.get('amount', 0)
                new_balance = data.get('balance', 0)
                logger.info(f"✅ SPIN SUCCESSFUL! Won: {win_amount} PKR | New Balance: {new_balance} PKR 🎉")
                
                # Save result with next spin time
                next_spin = self.calculate_next_spin_time()
                with open('spin_results.json', 'a') as f:
                    f.write(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'amount': win_amount,
                        'balance': new_balance,
                        'status': 'success',
                        'next_spin_available': datetime.fromtimestamp(next_spin).isoformat() if next_spin else None
                    }) + '\n')
                
                return True
            else:
                error = data.get('error', 'Unknown error')
                logger.warning(f"⚠️  Spin failed: {error}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Spin request failed: {e}")
            return False
    
    def save_next_spin_info(self):
        """Save next spin time for scheduling reference"""
        next_spin = self.calculate_next_spin_time()
        if next_spin:
            remaining_seconds = next_spin - int(time.time())
            hours = remaining_seconds // 3600
            minutes = (remaining_seconds % 3600) // 60
            
            info = {
                'next_spin_timestamp': next_spin,
                'next_spin_datetime': datetime.fromtimestamp(next_spin).isoformat(),
                'hours_until_spin': hours,
                'minutes_until_spin': minutes,
                'total_seconds_until_spin': remaining_seconds,
                'saved_at': datetime.now().isoformat()
            }
            with open('next_spin_info.json', 'w') as f:
                json.dump(info, f, indent=2)
            logger.info(f"📝 Next spin: {info['next_spin_datetime']} ({hours}h {minutes}m remaining)")
    
    def run(self):
        """Main bot logic"""
        logger.info("=" * 60)
        logger.info(f"🚀 SpinPK Bot Started at {datetime.now()}")
        logger.info(f"📱 Device: {self.device_id}")
        logger.info("=" * 60)
        
        try:
            # Step 1: Get user data
            if not self.get_user_data():
                logger.error("❌ Failed to fetch user data! Exiting...")
                return False
            
            # Step 2: Save next spin info
            self.save_next_spin_info()
            
            # Step 3: Check if can spin
            if not self.can_spin():
                logger.info("⏳ Spin not available yet. Waiting...")
                return True
            
            # Step 4: Perform spin
            if not self.spin():
                logger.warning("⚠️  Spin attempt failed!")
                return False
            
            logger.info("=" * 60)
            logger.info("✅ Bot execution completed successfully!")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    try:
        bot = SpinPKBot()
        success = bot.run()
        exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Failed to initialize bot: {e}")
        exit(1)
