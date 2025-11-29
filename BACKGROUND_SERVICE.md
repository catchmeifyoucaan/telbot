# Running ATLAS as a Background Service

This guide shows you **3 methods** to run ATLAS 24/7 in the background, even when you close the terminal or log out.

---

## ⭐ **Method 1: Systemd Service (RECOMMENDED)**

**Best for:** Production use, auto-restart on crashes, starts automatically on server boot

### Installation

```bash
# 1. Copy service file to systemd directory
sudo cp /root/telbot/atlas.service /etc/systemd/system/

# 2. Reload systemd
sudo systemctl daemon-reload

# 3. Enable ATLAS to start on boot
sudo systemctl enable atlas

# 4. Start ATLAS service
sudo systemctl start atlas
```

### Management Commands

```bash
# Check status
sudo systemctl status atlas

# View live logs
sudo journalctl -u atlas -f

# View all logs
sudo journalctl -u atlas

# Stop ATLAS
sudo systemctl stop atlas

# Restart ATLAS
sudo systemctl restart atlas

# Disable auto-start on boot
sudo systemctl disable atlas
```

### Example Usage

```bash
# Start the service
sudo systemctl start atlas

# Check it's running
sudo systemctl status atlas
# You should see: Active: active (running)

# Watch logs in real-time
sudo journalctl -u atlas -f

# Now go to Telegram and send commands!
```

**✅ Benefits:**
- Auto-restart if crash
- Starts on server reboot
- Proper logging with journalctl
- Easy to manage
- Production-grade

---

## 🚀 **Method 2: Screen (Easy & Quick)**

**Best for:** Quick deployment, easy monitoring, temporary sessions

### Installation

```bash
# Install screen (if not already installed)
sudo apt-get install screen -y
```

### Start ATLAS in Screen

```bash
# 1. Start a new screen session named 'atlas'
screen -S atlas

# 2. Navigate to project directory
cd /root/telbot

# 3. Run ATLAS
python3 atlas_agent.py

# 4. Detach from screen (ATLAS keeps running)
# Press: Ctrl+A, then D
```

### Management Commands

```bash
# List all screen sessions
screen -ls

# Reattach to ATLAS session (to see logs)
screen -r atlas

# Kill the session (stops ATLAS)
screen -X -S atlas quit
```

### Example Workflow

```bash
# Start ATLAS
screen -S atlas
cd /root/telbot
python3 atlas_agent.py

# Detach: Press Ctrl+A then D
# ATLAS is now running in background!

# Close terminal - ATLAS keeps running!

# Later, check on it:
screen -r atlas

# Detach again: Ctrl+A then D
```

**✅ Benefits:**
- Very easy to use
- Can reattach to see live output
- No configuration needed
- Works everywhere

---

## 💨 **Method 3: nohup (Simplest)**

**Best for:** Quick one-liners, minimal setup

### Start ATLAS with nohup

```bash
# Navigate to project directory
cd /root/telbot

# Run ATLAS in background
nohup python3 atlas_agent.py > logs/atlas.log 2>&1 &

# Get the process ID
echo $!
```

### Management Commands

```bash
# View logs
tail -f /root/telbot/logs/atlas.log

# Find ATLAS process
ps aux | grep atlas_agent.py

# Stop ATLAS (replace PID with actual process ID)
kill <PID>

# Force stop if needed
kill -9 <PID>
```

### Example Usage

```bash
# Create logs directory
mkdir -p /root/telbot/logs

# Start ATLAS
cd /root/telbot
nohup python3 atlas_agent.py > logs/atlas.log 2>&1 &

# Save the process ID shown
# Example output: [1] 12345

# View logs
tail -f logs/atlas.log

# Stop ATLAS later
kill 12345
```

**✅ Benefits:**
- Simplest method
- No additional software needed
- Good for testing

**❌ Limitations:**
- No auto-restart on crash
- Manual process management
- Harder to monitor

---

## 📊 **Comparison**

| Feature | Systemd | Screen | nohup |
|---------|---------|--------|-------|
| **Ease of Setup** | Medium | Easy | Very Easy |
| **Auto-restart on crash** | ✅ Yes | ❌ No | ❌ No |
| **Start on boot** | ✅ Yes | ❌ No | ❌ No |
| **View live output** | ✅ journalctl | ✅ Reattach | ❌ tail -f only |
| **Best for** | Production | Development | Quick tests |
| **Process management** | ✅ Excellent | ⚠️ Manual | ⚠️ Manual |

---

## 🎯 **Recommended Setup**

### For Production / Long-term Use:
```bash
sudo cp /root/telbot/atlas.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable atlas
sudo systemctl start atlas
sudo journalctl -u atlas -f
```

### For Quick Testing:
```bash
screen -S atlas
cd /root/telbot
python3 atlas_agent.py
# Press Ctrl+A then D to detach
```

---

## 🔍 **Troubleshooting**

### Check if ATLAS is running

**Systemd:**
```bash
sudo systemctl status atlas
```

**Screen:**
```bash
screen -ls
```

**nohup:**
```bash
ps aux | grep atlas_agent.py
```

### View Logs

**Systemd:**
```bash
sudo journalctl -u atlas -n 100  # Last 100 lines
sudo journalctl -u atlas -f      # Follow (live)
```

**Screen:**
```bash
screen -r atlas  # Reattach to see output
```

**nohup:**
```bash
tail -f /root/telbot/logs/atlas.log
```

### Restart ATLAS

**Systemd:**
```bash
sudo systemctl restart atlas
```

**Screen:**
```bash
screen -X -S atlas quit  # Stop
screen -S atlas          # Start new session
cd /root/telbot && python3 atlas_agent.py
```

**nohup:**
```bash
kill <PID>  # Stop
nohup python3 atlas_agent.py > logs/atlas.log 2>&1 &  # Start
```

---

## 🛡️ **Security Notes**

1. **Protect your .env file:**
   ```bash
   chmod 600 /root/telbot/.env
   ```

2. **Secure log files:**
   ```bash
   chmod 700 /root/telbot/logs
   ```

3. **Run as dedicated user (optional):**
   Edit `atlas.service` and change `User=root` to a dedicated user

---

## ✅ **Quick Start (Systemd - Recommended)**

Copy and paste this entire block:

```bash
cd /root/telbot
sudo cp atlas.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable atlas
sudo systemctl start atlas
sudo systemctl status atlas
```

**Done!** ATLAS is now running 24/7 in the background.

Test it by sending `.atlas @TechCrunch 50` in Telegram Saved Messages.

---

## 📱 **Usage After Setup**

Once ATLAS is running in the background:

1. **Open Telegram**
2. **Go to Saved Messages**
3. **Send commands:**
   ```
   .atlas @channel 100
   .watch @channel crypto,scam
   .compare @news1 @news2
   ```

ATLAS responds automatically - no need to keep terminal open!
