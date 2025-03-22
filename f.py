import requests
import json
import time
import sys
import random
from datetime import datetime, timedelta
from colorama import Fore, Style, init

init(autoreset=True)

# Constants
BASE_URL = "https://api.flow3.tech/api/v1"
MTCADMIN_API_URL = "https://api.mtcadmin.click/api/v1"
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://dashboard.flow3.tech",
    "referer": "https://dashboard.flow3.tech/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}
WAIT_TIME = 5  # Jeda 5 detik antar akun
TIMER_DURATION = 86400  # 24 jam dalam detik

def print_welcome_message():
    """Print welcome banner for the application"""
    print(Fore.WHITE + r"""
_  _ _   _ ____ ____ _    ____ _ ____ ___  ____ ____ ___ 
|\ |  \_/  |__| |__/ |    |__| | |__/ |  \ |__/ |  | |__]
| \|   |   |  | |  \ |    |  | | |  \ |__/ |  \ |__| |         
          """)
    print(Fore.GREEN + Style.BRIGHT + "Nyari Airdrop  Flow3 Network")
    print(Fore.YELLOW + Style.BRIGHT + "Telegram: https://t.me/nyariairdrop\n")

def load_proxies(filename):
    """Load proxies from a file, handling both authenticated and simple proxies"""
    try:
        with open(filename, 'r') as file:
            proxies = []
            for line in file:
                line = line.strip()
                if line:
                    parts = line.split(":")
                    if len(parts) == 4:
                        ip, port, user, password = parts
                        proxy_url = f"http://{user}:{password}@{ip}:{port}"
                    elif len(parts) == 2:
                        ip, port = parts
                        proxy_url = f"http://{ip}:{port}"
                    else:
                        continue
                    proxies.append(proxy_url)
        
        if proxies:
            print(Fore.BLUE + f"Berhasil memuat {len(proxies)} proxy.")
        return proxies
    except FileNotFoundError:
        print(Fore.YELLOW + f"File {filename} tidak ditemukan. Melanjutkan tanpa proxy.")
        return []

def get_proxy(proxies):
    """Retrieve a random proxy"""
    if not proxies:
        return None
    proxy_url = random.choice(proxies)
    return {"http": proxy_url, "https": proxy_url}

def load_accounts_from_data_txt():
    """Load wallet addresses and tokens directly from data.txt file"""
    accounts = []
    try:
        with open("data.txt", "r") as file:
            lines = file.readlines()
            
            # Process the file in pairs of lines
            for i in range(0, len(lines), 2):
                if i + 1 < len(lines):  # Ensure we have both address and token
                    wallet_address = lines[i].strip()
                    token = lines[i+1].strip()
                    
                    if wallet_address and token:  # Make sure neither is empty
                        accounts.append((wallet_address, token))
        
        print(Fore.GREEN + f"✔ Berhasil memuat {len(accounts)} akun dari data.txt")
        return accounts
    except FileNotFoundError:
        print(Fore.RED + "✖ File data.txt tidak ditemukan.")
        print(Fore.YELLOW + "Format data.txt harus berupa 2 baris per akun: baris pertama adalah alamat Solana, baris kedua adalah token.")
        sys.exit(1)
    except Exception as e:
        print(Fore.RED + f"✖ Terjadi kesalahan saat membaca data.txt: {str(e)}")
        sys.exit(1)

def get_tasks(token, proxies):
    """Get available tasks for the account"""
    headers = HEADERS.copy()
    headers["authorization"] = f"Bearer {token}"
    response = requests.get(f"{BASE_URL}/tasks/", headers=headers, proxies=get_proxy(proxies))
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print(Fore.RED + "Gagal mengambil tugas.")
        return []

def complete_task(task, token, proxies):
    """Complete a specific task for the account"""
    if task["status"] == 1:
        print(Fore.YELLOW + f"✔ Tugas {task['taskId']} sudah diselesaikan sebelumnya.")
        return
    
    headers = HEADERS.copy()
    headers["authorization"] = f"Bearer {token}"
    response = requests.post(f"{BASE_URL}/tasks/{task['taskId']}/complete", headers=headers, proxies=get_proxy(proxies))
    if response.status_code == 200:
        print(Fore.GREEN + f"✔ Tugas {task['taskId']} berhasil diselesaikan!")
    else:
        print(Fore.RED + f"✖ Gagal menyelesaikan tugas {task['taskId']}: {response.text}")

def complete_all_tasks(token, proxies):
    """Complete all available tasks for the account"""
    tasks = get_tasks(token, proxies)
    for task in tasks:
        complete_task(task, token, proxies)

def get_daily_check_in(token, proxies):
    """Check daily check-in status and determine if check-in is needed today"""
    headers = HEADERS.copy()
    headers["authorization"] = f"Bearer {token}"

    response = requests.get(f"{BASE_URL}/tasks/daily", headers=headers, proxies=get_proxy(proxies))
    
    if response.status_code == 200:
        daily_tasks = response.json().get("data", [])
        
        # Find the first incomplete day
        current_day = None
        completed_days = []
        
        for task in daily_tasks:
            day_num = int(task["title"].split()[-1])
            
            if task["status"] == 1:
                completed_days.append(str(day_num))
            elif current_day is None:
                # This is the first incomplete day
                current_day = day_num
        
        if current_day is None:
            # All days completed
            print(Fore.GREEN + "✓ Semua hari check-in sudah selesai!")
            return False
        
        # Check if any completed days
        if completed_days:
            print(Fore.GREEN + f"✓ Sudah check-in hari: {', '.join(completed_days)}")
        
        print(Fore.YELLOW + f"⏳ Perlu check-in untuk Hari {current_day}")
        return True
    else:
        print(Fore.RED + f"✖ Gagal mengambil status check-in harian: {response.text}")
        return False

def check_in_daily(token, proxies):
    """Perform daily check-in if needed"""
    # Check if we need to do a check-in today
    needs_checkin = get_daily_check_in(token, proxies)
    
    if not needs_checkin:
        return  # No check-in needed
    
    headers = HEADERS.copy()
    headers["authorization"] = f"Bearer {token}"

    response = requests.post(f"{BASE_URL}/tasks/complete-daily", headers=headers, proxies=get_proxy(proxies))

    if response.status_code == 200:
        print(Fore.GREEN + "✓ Check-in harian berhasil!")
    else:
        error_data = response.json()
        if error_data.get("statusCode") == 400 and "Already checkin" in error_data.get("message", ""):
            print(Fore.YELLOW + "✓ Sudah melakukan check-in hari ini.")
        else:
            print(Fore.RED + f"✖ Gagal check-in harian: {response.text}")

def countdown_timer(duration):
    """Countdown timer before restarting the script"""
    end_time = datetime.now() + timedelta(seconds=duration)
    while datetime.now() < end_time:
        remaining = end_time - datetime.now()
        sys.stdout.write(f"\r⏳ Memulai ulang dalam: {remaining}".split('.')[0] + " " * 10)
        sys.stdout.flush()
        time.sleep(1)
    print("\n🔄 Memulai ulang sekarang!")

def share_bandwidth(token, proxies):
    """Share bandwidth to earn points"""
    headers = HEADERS.copy()
    headers["authorization"] = f"Bearer {token}"
    
    response = requests.post(
        f"{MTCADMIN_API_URL}/bandwidth",
        headers=headers,
        json={},
        proxies=get_proxy(proxies)
    )
    
    if response.status_code == 200:
        data = response.json().get("data", {})
        
        # Format the bandwidth sharing information nicely
        print(Fore.GREEN + "📡 Bandwidth Sharing:")
        
        if data:
            # If there's data in the response, display it in a structured way
            for key, value in data.items():
                formatted_key = key.replace('_', ' ').title()
                print(Fore.CYAN + f"  ├─ {formatted_key}: {value}")
        else:
            # If no detailed data, just show success message
            print(Fore.CYAN + "  └─ Status: Berhasil")
            
        return {"success": True, "data": data}
    else:
        # Error handling
        try:
            error_data = response.json()
            error_message = error_data.get("message", "Unknown error")
            status_code = error_data.get("statusCode", response.status_code)
            
            if "already" in error_message.lower():
                print(Fore.YELLOW + "📡 Bandwidth Sharing: Sudah dibagikan sebelumnya")
            else:
                print(Fore.RED + f"✖ Bandwidth Sharing gagal: {error_message} (Code: {status_code})")
        except:
            print(Fore.RED + f"✖ Bandwidth Sharing gagal: {response.text}")
            
        return {"success": False, "error": response.text}

def get_point_info(token, proxies):
    """Get point information for the account"""
    headers = HEADERS.copy()
    headers["authorization"] = f"Bearer {token}"
    
    response = requests.get(
        f"{MTCADMIN_API_URL}/point/info",
        headers=headers,
        proxies=get_proxy(proxies)
    )
    
    if response.status_code == 200:
        data = response.json().get("data", {})
        
        # Format the point information nicely
        total_points = data.get('totalEarningPoint', 0)
        today_points = data.get('todayEarningPoint', 0)
        referral_points = data.get('referralEarningPoint', 0)
        
        print(Fore.GREEN + "📊 Informasi Poin:")
        print(Fore.CYAN + f"  ├─ Total Poin: {total_points}")
        print(Fore.CYAN + f"  ├─ Poin Hari Ini: {today_points}")
        print(Fore.CYAN + f"  └─ Poin Referral: {referral_points}")
        
        return {"success": True, "data": data}
    else:
        error_message = f"Get point info failed: {response.text}"
        print(Fore.RED + f"✖ {error_message}")
        return {"success": False, "error": error_message}

def main():
    print_welcome_message()
    proxies = load_proxies("proxy.txt")
    accounts = load_accounts_from_data_txt()
    print(Fore.CYAN + f"📌 Total akun: {len(accounts)}")
    
    for i, (wallet, token) in enumerate(accounts, 1):
        print("\n" + "=" * 50)
        print(Fore.CYAN + f"➡ Memproses akun {i}/{len(accounts)}: {wallet[:8]}...{wallet[-6:]}")
        print("-" * 50)
        
        # Coba beberapa kali jika terjadi error sementara
        for attempt in range(3):
            try:
                complete_all_tasks(token, proxies)
                check_in_daily(token, proxies)
                share_bandwidth(token, proxies)
                get_point_info(token, proxies)
                break  # Jika sukses, keluar dari loop retry
            except Exception as e:
                print(Fore.RED + f"⚠ Terjadi kesalahan, mencoba ulang ({attempt+1}/3): {str(e)}")
                time.sleep(3)  # Jeda sebelum mencoba lagi
        
        # Tunggu lebih singkat antara akun
        if i < len(accounts):
            account_delay = random.randint(60, 180)  # 1-3 menit
            print(Fore.YELLOW + f"⏳ Menunggu {account_delay} detik sebelum akun berikutnya...")
            time.sleep(account_delay)
    
    print("\n" + "=" * 50)
    print(Fore.GREEN + "✅ Semua tugas dan aktivitas untuk semua akun selesai.")
    
    # Siklus berbagi bandwidth dengan optimasi jumlah sharing
    end_time = datetime.now() + timedelta(seconds=TIMER_DURATION)
    
    try:
        while datetime.now() < end_time:
            random.shuffle(accounts)  
            
            for wallet, token in accounts:
                sharing_count = random.randint(5, 10)  # Tingkatkan jumlah sharing
                print("\n" + "-" * 50)
                print(Fore.CYAN + f"🔄 Berbagi bandwidth {sharing_count} kali untuk akun {wallet[:8]}...{wallet[-6:]}")
                
                successful_shares = 0
                for share_attempt in range(sharing_count):
                    print(Fore.YELLOW + f"  ⏳ Mencoba berbagi bandwidth ke-{share_attempt+1}/{sharing_count}...")
                    result = share_bandwidth(token, proxies)
                    
                    if result["success"]:
                        successful_shares += 1
                    
                    # Tunggu lebih singkat antara sharing
                    if share_attempt < sharing_count - 1:
                        share_delay = random.randint(20, 60)  # 20-60 detik
                        time.sleep(share_delay)
                
                # Cek ulang poin setelah berbagi lebih banyak bandwidth
                get_point_info(token, proxies)
                
                # Tunggu antar akun lebih singkat
                if wallet != accounts[-1][0]:
                    account_delay = random.randint(90, 300)  # 1.5-5 menit
                    print(Fore.YELLOW + f"⏳ Menunggu {account_delay} detik sebelum akun berikutnya...")
                    time.sleep(account_delay)
            
            remaining = (end_time - datetime.now()).total_seconds()
            if remaining <= 0:
                break
            
            max_wait = min(random.randint(1200, 2400), remaining)  # 20-40 menit
            print("\n" + "=" * 50)
            print(Fore.GREEN + f"✅ Siklus berbagi bandwidth selesai, menunggu {int(max_wait/60)} menit...")
            time.sleep(max_wait)
        
        print("\n" + "=" * 50)
        print(Fore.GREEN + "⏰ 24 jam telah berlalu. Memulai ulang siklus penuh...")
        main()
    except KeyboardInterrupt:
        print(Fore.RED + "\n✖ Program dihentikan oleh pengguna.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.RED + "\n✖ Program dihentikan oleh pengguna.")
        sys.exit(1)
    except Exception as e:
        print(Fore.RED + f"⚠ Terjadi kesalahan fatal: {str(e)}")
