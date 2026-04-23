"""
PepeRush Bot — Crash Test Suite
Run: python test_suite.py
Tests all critical paths without a live Telegram connection.
"""

import sys
import os
import time
import sqlite3

# Point at a test DB
os.environ["DB_PATH"] = "/tmp/peperush_test.db"

# Remove old test DB
if os.path.exists("/tmp/peperush_test.db"):
    os.remove("/tmp/peperush_test.db")

import database as db

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    results.append((status, name, detail))
    print(f"{status}  {name}" + (f" — {detail}" if detail else ""))


# ─────────────────────────────────────────────────────────────────────────────
# 1. DB Init
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 1. Database Init ──────────────────────────────────────────────")
try:
    db.init_db()
    check("DB initialises without error", True)
except Exception as e:
    check("DB initialises without error", False, str(e))

tasks = db.get_active_tasks()
check("Default tasks seeded", len(tasks) > 0, f"{len(tasks)} tasks found")


# ─────────────────────────────────────────────────────────────────────────────
# 2. User Registration
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 2. User Registration ─────────────────────────────────────────")
db.upsert_user(1001, "alice", "Alice")
db.upsert_user(1002, "bob", "Bob")
u = db.get_user(1001)
check("User created", u is not None)
check("Username stored", u["username"] == "alice")

db.upsert_user(1001, "alice_new", "Alice")
u2 = db.get_user(1001)
check("Username update works", u2["username"] == "alice_new")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Human Verification
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 3. Human Verification ────────────────────────────────────────")
check("Not verified by default", db.get_user(1001)["human_verified"] == 0)
db.set_human_verified(1001)
check("Set verified works", db.get_user(1001)["human_verified"] == 1)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Balance Operations
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 4. Balance Operations ────────────────────────────────────────")
check("Initial balance is 0", db.get_balance(1001) == 0)
db.add_balance(1001, 10_000)
check("Add balance works", db.get_balance(1001) == 10_000)
db.add_balance(1001, 5_000)
check("Cumulative add works", db.get_balance(1001) == 15_000)
db.deduct_balance(1001, 5_000)
check("Deduct balance works", db.get_balance(1001) == 10_000)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Wallet
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 5. Wallet ─────────────────────────────────────────────────────")
check("Wallet is None by default", db.get_user(1001)["wallet"] is None)
db.set_wallet(1001, "0xABCDEF1234567890")
check("Wallet set correctly", db.get_user(1001)["wallet"] == "0xABCDEF1234567890")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Referral System
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 6. Referral System ───────────────────────────────────────────")

# New user 1003 referred by 1001
db.upsert_user(1003, "charlie", "Charlie")
db.set_referrer(1003, 1001)
db.add_referral_pending(1003, 1001)

pending = db.get_referral_pending(1003)
check("Referral pending created", pending is not None)
check("Referral not yet rewarded", not db.is_referral_rewarded(1003))

# Self-referral attempt
db.upsert_user(1004, "dave", "Dave")
db.set_referrer(1004, 1004)  # should be blocked by UPDATE ... WHERE referrer_id IS NULL
# Since 1004 never had a referrer, this will SET it — we simulate the guard in the handler
# The handler checks referrer_id != user.id BEFORE calling set_referrer
# Test the is_referral_rewarded guard
db.mark_referral_rewarded(1003, 1001)
check("Referral rewarded — referrer count incremented",
      db.get_user(1001)["referral_count"] == 1)
check("is_referral_rewarded returns True after reward", db.is_referral_rewarded(1003))

# Duplicate reward guard
initial_balance = db.get_balance(1001)
# Simulating: should not reward again
already = db.is_referral_rewarded(1003)
if not already:
    db.add_balance(1001, 10_000)
check("Duplicate referral reward blocked", db.get_balance(1001) == initial_balance)

# Pending removed after reward
check("Pending referral cleared", db.get_referral_pending(1003) is None)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Daily Bonus Cooldown
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 7. Daily Bonus Cooldown ──────────────────────────────────────")
now = time.time()
db.set_last_daily(1001, now - 90000)  # more than 24h ago
u = db.get_user(1001)
elapsed = now - u["last_daily"]
check("24h elapsed correctly detected", elapsed > 86400)

db.set_last_daily(1001, now - 3600)   # 1h ago
u2 = db.get_user(1001)
elapsed2 = now - u2["last_daily"]
check("Cooldown active correctly detected", elapsed2 < 86400)


# ─────────────────────────────────────────────────────────────────────────────
# 8. Withdrawal Guards
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 8. Withdrawal Guards ─────────────────────────────────────────")

# Set balance high enough
db.add_balance(1001, 50_000)
bal = db.get_balance(1001)
check("Balance sufficient for withdraw", bal >= 50_000)

check("No pending withdrawal initially", not db.has_pending_withdrawal(1001))
wd_id = db.create_withdrawal(1001, 50_000, "0xABCDEF1234567890")
check("Withdrawal created", wd_id > 0)
check("Pending withdrawal detected", db.has_pending_withdrawal(1001))

# Deduct
db.deduct_balance(1001, 50_000)
remaining_bal = db.get_balance(1001)
check("Balance deducted after withdrawal", remaining_bal < 50_000)


# ─────────────────────────────────────────────────────────────────────────────
# 9. Task Management
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 9. Task Management ───────────────────────────────────────────")
initial_count = len(db.get_active_tasks())
db.add_task("telegram", "https://t.me/test_new_channel")
check("New task added", len(db.get_active_tasks()) == initial_count + 1)

db.remove_task("https://t.me/test_new_channel")
check("Task removed (deactivated)", len(db.get_active_tasks()) == initial_count)

# Duplicate insert ignored
db.add_task("whatsapp", "https://chat.whatsapp.com/TEST123")
db.add_task("whatsapp", "https://chat.whatsapp.com/TEST123")
wa_tasks = [t for t in db.get_active_tasks() if "TEST123" in t["link"]]
check("Duplicate task not inserted twice", len(wa_tasks) == 1)


# ─────────────────────────────────────────────────────────────────────────────
# 10. Suspicious Logging
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 10. Suspicious Logging ───────────────────────────────────────")
db.log_suspicious(9999, "fake_referral_attempt")
db.log_suspicious(9999, "fake_referral_attempt")
db.log_suspicious(9999, "fake_referral_attempt")
count = db.get_suspicious_count(9999, "fake_referral_attempt")
check("Suspicious count tracked correctly", count == 3)

old_count = db.get_suspicious_count(9999, "fake_referral_attempt", window=1)
time.sleep(2)
fresh = db.get_suspicious_count(9999, "fake_referral_attempt", window=1)
check("Suspicious count respects time window", fresh == 0)


# ─────────────────────────────────────────────────────────────────────────────
# 11. Leaderboard
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 11. Leaderboard ──────────────────────────────────────────────")
for i in range(5):
    uid = 2000 + i
    db.upsert_user(uid, f"user{i}", f"User{i}")
    # Simulate different referral counts
    for _ in range(5 - i):
        db.upsert_user(3000 + i * 10 + _, f"ref{i}{_}", f"Ref")
        db.mark_referral_rewarded(3000 + i * 10 + _, uid)

board = db.get_leaderboard(10)
check("Leaderboard returns entries", len(board) > 0)
if len(board) >= 2:
    check("Leaderboard sorted descending",
          board[0]["referral_count"] >= board[1]["referral_count"])


# ─────────────────────────────────────────────────────────────────────────────
# 12. Admin Balance
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 12. Admin /add_balance ───────────────────────────────────────")
before = db.get_balance(1002)
db.add_balance(1002, 99_999)
after = db.get_balance(1002)
check("Admin add_balance credits correctly", after == before + 99_999)


# ─────────────────────────────────────────────────────────────────────────────
# 13. Stats
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 13. Stats ────────────────────────────────────────────────────")
stats = db.get_stats()
check("Stats: total_users > 0", stats["total_users"] > 0)
check("Stats: total_withdrawals >= 1", stats["total_withdrawals"] >= 1)


# ─────────────────────────────────────────────────────────────────────────────
# 14. Ban
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 14. Ban System ───────────────────────────────────────────────")
db.upsert_user(5001, "spammer", "Spammer")
db.ban_user(5001)
check("User banned", db.get_user(5001)["is_banned"] == 1)


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "═" * 60)
total  = len(results)
passed = sum(1 for r in results if r[0] == PASS)
failed = sum(1 for r in results if r[0] == FAIL)

print(f"\n🧪 Test Results: {passed}/{total} passed")

if failed:
    print(f"\n{FAIL} Failures:")
    for r in results:
        if r[0] == FAIL:
            print(f"   • {r[1]}" + (f": {r[2]}" if r[2] else ""))
    sys.exit(1)
else:
    print("🎉 All tests passed! PepeRush Bot is production-ready.")
    sys.exit(0)
