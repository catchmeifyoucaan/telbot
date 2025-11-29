# 🚀 Run ATLAS in Background - Super Simple Guide

## **Option 1: One-Line Install (EASIEST) ⭐**

Just run this single command:

```bash
cd /root/telbot && sudo ./install_service.sh
```

**That's it!** ATLAS is now running 24/7 in the background.

### What this does:
- ✅ Installs ATLAS as a system service
- ✅ Starts ATLAS automatically
- ✅ Auto-restart if it crashes
- ✅ Starts on server boot
- ✅ Runs even when you close terminal

---

## **Option 2: Screen (Quick & Easy)**

```bash
# Install screen
sudo apt-get install screen -y

# Start ATLAS in background
screen -S atlas
cd /root/telbot
python3 atlas_agent.py

# Press: Ctrl+A then D (to detach)
# Done! Close terminal safely.
```

**To check on it later:**
```bash
screen -r atlas  # View logs
# Press Ctrl+A then D to detach again
```

---

## **How to Use After Setup**

1. **Open Telegram app**
2. **Go to "Saved Messages"**
3. **Send commands:**

```
.atlas @TechCrunch 50

.atlas @channel 100 --media --entities --export json

.watch @channel crypto,scam,urgent

.compare @news1 @news2 100
```

**ATLAS responds automatically!**

---

## **Management Commands (Option 1 - Systemd)**

```bash
# View live logs
sudo journalctl -u atlas -f

# Check status
sudo systemctl status atlas

# Restart
sudo systemctl restart atlas

# Stop
sudo systemctl stop atlas
```

---

## **Management Commands (Option 2 - Screen)**

```bash
# Check if running
screen -ls

# View logs
screen -r atlas

# Stop ATLAS
screen -X -S atlas quit
```

---

## **Verify It's Working**

After installation:

1. **Check status:**
   ```bash
   sudo systemctl status atlas
   ```
   Should say: `Active: active (running)`

2. **View logs:**
   ```bash
   sudo journalctl -u atlas -f
   ```
   Should show: `Atlas Online. Logged in as...`

3. **Test in Telegram:**
   - Open Saved Messages
   - Send: `.atlas @TechCrunch 20`
   - Get AI analysis back!

---

## **Troubleshooting**

### ATLAS not starting?

**Check logs:**
```bash
sudo journalctl -u atlas -n 50
```

**Common issues:**

1. **Missing .env file**
   - Make sure `/root/telbot/.env` exists with your API keys

2. **Missing dependencies**
   ```bash
   cd /root/telbot
   pip install -r requirements.txt
   ```

3. **Wrong Python path**
   ```bash
   which python3
   # Update atlas.service if needed
   ```

### Restart everything:
```bash
sudo systemctl restart atlas
sudo journalctl -u atlas -f
```

---

## **Quick Reference**

| Task | Command |
|------|---------|
| **Install** | `cd /root/telbot && sudo ./install_service.sh` |
| **View logs** | `sudo journalctl -u atlas -f` |
| **Check status** | `sudo systemctl status atlas` |
| **Restart** | `sudo systemctl restart atlas` |
| **Stop** | `sudo systemctl stop atlas` |
| **Uninstall** | `sudo systemctl stop atlas && sudo systemctl disable atlas` |

---

## **Complete Setup Example**

```bash
# 1. Navigate to project
cd /root/telbot

# 2. Make sure .env is configured
cat .env

# 3. Install as background service
sudo ./install_service.sh

# 4. View logs (optional)
sudo journalctl -u atlas -f

# 5. Open Telegram → Saved Messages → Send commands!
```

**Done! ATLAS runs forever in background.**

---

## **Need More Details?**

See `BACKGROUND_SERVICE.md` for complete documentation of all methods.
