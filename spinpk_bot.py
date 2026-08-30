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
        self.email = os.getenv('SPINPK_EMAIL')
        self.password = os.getenv('SPINPK_PASSWORD')
        self.device_id = os.getenv('SPINPK_DEVICE_ID', 'f607b24295e557fe')
        self.base_url = 'https://spinpk.net/api'
        self.token = None
        self.user_data = None
        self.config = None
        self.session = requests.Session()
        
        # Validation
        if not self.email or not self.password:
            logger.error("❌ SPINPK_EMAIL and SPINPK_PASSWORD must be set!")
            raise ValueError("Missing credentials")
        
    def get_headers(self, token=None):
        """Generate headers for API requests"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Infinix X659B Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/152.0.7977.42 Mobile Safari/537.36',
            'Content-Type': 'application/json',
            'X-Device-Id': self.device_id,
            'X-Requested-With': 'com.spinpk.app',
            'Accept': '*/*',
            'Origin': 'null'
        }
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        return headers
    
    def login(self):
        """Login with email/password and get fresh token"""
        logger.info("🔄 Logging in with email/password...")
        
        try:
            url = f'{self.base_url}/auth.php'
            
            payload = {
                "action": "login",
                "email": self.email,
                "password": self.password
            }
            
            response = self.session.post(
                url,
                headers=self.get_headers(),
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('ok') and 'token' in data:
                self.token = data['token']
                logger.info(f"✅ Login successful! Token: {self.token[:30]}...")
                return True
            else:
                error = data.get('error', data.get('message', 'Unknown error'))
                logger.error(f"❌ Login failed: {error}")
                if 'update' in error.lower():
                    logger.error("⚠️  API requires app update - credentials may be outdated!")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Login request failed: {e}")
            return False
    
    def get_user_data(self):
        """Get user info and config"""
        logger.info("📊 Fetching user data...")
        
        try:
            url = f'{self.base_url}/auth.php'
            
            payload = {"action": "me"}
            
            response = self.session.post(
                url,
                headers=self.get_headers(self.token),
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('ok'):
                self.user_data = data.get('user', {})
                self.config = data.get('config', {})
                
                logger.info(f"✅ User: {self.user_data.get('name', 'Unknown')}")
                logger.info(f"💰 Balance: {self.user_data.get('balance')} PKR")
                logger.info(f"🎡 Last spin: {self.user_data.get('last_spin_at')}")
                
                return True
            else:
                logger.error(f"❌ Failed to get user data: {data}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request failed: {e}")
            return False
    
    def calculate_next_spin_time(self):
        """Calculate when next spin will be available"""
        if not self.user_data or not self.config:
            return None
        
        last_spin = self.user_data.get('last_spin_at', 0)
        spin_interval = self.config.get('spin_interval_sec', 7200)  # Default 2 hours
        
        next_spin_time = last_spin + spin_interval
        return next_spin_time
    
    def can_spin(self):
        """Check if user can spin"""
        if not self.user_data:
            return False
        
        last_spin = self.user_data.get('last_spin_at', 0)
        spin_interval = self.config.get('spin_interval_sec', 7200)
        current_time = int(time.time())
        
        time_since_spin = current_time - last_spin
        
        logger.info(f"⏱️  Last spin: {datetime.fromtimestamp(last_spin)}")
        logger.info(f"⏱️  Spin interval: {spin_interval} seconds ({spin_interval//3600} hours {(spin_interval%3600)//60} minutes)")
        logger.info(f"⏱️  Time since last spin: {time_since_spin} seconds")
        
        if time_since_spin >= spin_interval:
            logger.info(f"✅ Can spin! ({time_since_spin}s >= {spin_interval}s)")
            return True
        else:
            wait_time = spin_interval - time_since_spin
            hours = wait_time // 3600
            minutes = (wait_time % 3600) // 60
            seconds = wait_time % 60
            logger.warning(f"⏳ Cannot spin yet. Wait {hours}h {minutes}m {seconds}s")
            return False
    
    def spin(self):
        """Perform spin action"""
        logger.info("🎡 Attempting to spin...")
        
        try:
            url = f'{self.base_url}/spin.php'
            
            payload = {"action": "spin"}
            
            response = self.session.post(
                url,
                headers=self.get_headers(self.token),
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('ok'):
                win_amount = data.get('amount', 0)
                logger.info(f"✅ SPIN SUCCESSFUL! Won: {win_amount} PKR 🎉")
                
                # Save result with next spin time
                next_spin = self.calculate_next_spin_time()
                with open('spin_results.json', 'a') as f:
                    f.write(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'amount': win_amount,
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
        """Save next spin time for external scheduling"""
        next_spin = self.calculate_next_spin_time()
        if next_spin:
            info = {
                'next_spin_timestamp': next_spin,
                'next_spin_datetime': datetime.fromtimestamp(next_spin).isoformat(),
                'hours_until_spin': (next_spin - int(time.time())) / 3600,
                'saved_at': datetime.now().isoformat()
            }
            with open('next_spin_info.json', 'w') as f:
                json.dump(info, f, indent=2)
            logger.info(f"📝 Next spin info saved: {info['next_spin_datetime']}")
    
    def run(self):
        """Main bot logic"""
        logger.info("=" * 60)
        logger.info(f"🚀 SpinPK Bot Started at {datetime.now()}")
        logger.info("=" * 60)
        
        try:
            # Step 1: Login
            if not self.login():
                logger.error("❌ Login failed! Exiting...")
                return False
            
            # Step 2: Get user data
            if not self.get_user_data():
                logger.error("❌ Failed to fetch user data! Exiting...")
                return False
            
            # Step 3: Save next spin info for scheduling reference
            self.save_next_spin_info()
            
            # Step 4: Check if can spin
            if not self.can_spin():
                logger.info("⏳ Waiting for next spin window...")
                return True
            
            # Step 5: Perform spin
            if not self.spin():
                logger.warning("⚠️  Spin attempt failed but bot continues...")
                return True
            
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
