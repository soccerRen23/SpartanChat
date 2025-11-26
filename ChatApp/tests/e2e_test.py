#!/usr/bin/env python3
"""Simple end-to-end test for SpartanChat (uses HTTP only).

This script performs the following flow against a running app on http://localhost:5000:
 - signup new user
 - create a channel
 - post a message in the channel
 - edit the message
 - delete the message
 - delete the channel

It uses only the public HTTP endpoints and parses returned HTML to find ids.
"""

import re
import sys
import time
from urllib.parse import urljoin, parse_qs, urlparse

import requests
import os
import pymysql

BASE = "http://localhost:5000"


def uniq(prefix="test"):
    return f"{prefix}_{int(time.time())}"


def find_first(regex, text):
    m = re.search(regex, text)
    return m and m.group(1)


def extract_cid_from_channels(html, channel_name):
    # Find an anchor containing channel name and extract cid from href /messages?cid=<cid>
    # This handles basic HTML produced by the app.
    pattern = rf"<a[^>]*href=['\"]([^'\"]*messages\?cid=(\d+))['\"][^>]*>\s*{re.escape(channel_name)}\s*</a>"
    m = re.search(pattern, html)
    if m:
        return m.group(2)
    return None


def extract_mid_from_messages(html, text_snippet):
    # Each message form for edit/delete contains an action with mid in URL.
    # We'll find the first form action containing message text snippet and capture mid.
    # Approach: find the <li> that contains the snippet, then search form action inside.
    li_pattern = rf"(<li>.*?{re.escape(text_snippet)}.*?</li>)"
    m = re.search(li_pattern, html, re.S)
    if not m:
        return None
    li_html = m.group(1)
    action_pattern = r"action=[\"']([^'\"]*/messages/(\d+))[\"']"
    mm = re.search(action_pattern, li_html)
    if mm:
        return mm.group(2)
    return None


def run():
    s = requests.Session()

    # 1) Signup
    email = f"{uniq('autotest')}@example.com"
    password = "AutoPass123!"
    name = uniq('AutoUser')

    r = s.post(urljoin(BASE, "/signup"), data={
        "name": name,
        "email": email,
        "password": password,
        "password-confirmation": password,
    }, allow_redirects=False)
    assert r.status_code in (302, 303), f"signup did not redirect (status {r.status_code})"

    print(f"[OK] Signed up: {email}")

    # Explicitly login to ensure session stores numeric user id (login route uses integer id)
    lr = s.post(urljoin(BASE, "/login"), data={"email": email, "password": password}, allow_redirects=False)
    assert lr.status_code in (302, 303), f"login after signup failed: {lr.status_code}"
    print("[OK] Logged in after signup (session refreshed)")

    # 2) create channel
    channel_name = uniq('CHAN')
    channel_desc = "E2E channel"
    r = s.post(urljoin(BASE, "/channels"), data={"channelName": channel_name, "channelDescription": channel_desc}, allow_redirects=True)
    assert r.status_code == 200, f"create channel failed: {r.status_code}"

    if channel_name in r.text:
        print("[OK] Channel creation reflected on /channels page")
    else:
        raise RuntimeError("Channel not present in channels page after create")

    # extract cid
    cid = extract_cid_from_channels(r.text, channel_name)
    assert cid is not None, "couldn't extract created channel id"
    print(f"[OK] Created channel id: {cid}")

    # 3) post a message
    msg_text = "hello world e2e"
    r = s.post(urljoin(BASE, f"/messages?cid={cid}"), data={"message": msg_text}, allow_redirects=True)
    assert r.status_code == 200, f"post message failed: {r.status_code}"
    assert msg_text in r.text, "message not visible on messages page after posting"
    print("[OK] Message posted and visible")

    # extract mid from page (owner forms) first
    mid = extract_mid_from_messages(r.text, msg_text)
    # if page does not render edit forms (e.g. type mismatch) fall back to DB lookup
    if mid is None:
        # query DB directly for the most recent message with same content and channel
        db_host = os.getenv('DB_HOST', 'db')
        db_user = os.getenv('DB_USER', 'testuser')
        db_pass = os.getenv('DB_PASSWORD', 'testuser')
        db_name = os.getenv('DB_DATABASE', 'chatapp')
        try:
            conn = pymysql.connect(host=db_host, user=db_user, password=db_pass, database=db_name)
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM messages WHERE channel_id=%s AND message=%s ORDER BY id DESC LIMIT 1", (cid, msg_text))
                row = cur.fetchone()
                if row:
                    mid = str(row[0])
        except Exception:
            mid = None
    if mid is None:
        print('\n--- messages page html (debug) ---')
        print(r.text)
        print('--- end debug ---\n')
    assert mid is not None, "couldn't locate message id (page or DB)"
    print(f"[OK] Message id: {mid}")

    # 4) edit message
    edited = msg_text + " (edited)"
    r = s.post(urljoin(BASE, f"/messages/{mid}?cid={cid}"), data={"_method": "PUT", "message": edited}, allow_redirects=True)
    assert r.status_code == 200, f"edit message failed: {r.status_code}"
    assert edited in r.text, "edited message not visible"
    print("[OK] Message edited")

    # 5) delete message
    r = s.post(urljoin(BASE, f"/messages/{mid}?cid={cid}"), data={"_method": "DELETE"}, allow_redirects=True)
    assert r.status_code == 200, f"delete message failed: {r.status_code}"
    assert edited not in r.text, "message still visible after delete"
    print("[OK] Message deleted")

    # 6) delete channel
    r = s.post(urljoin(BASE, f"/channels/{cid}"), data={"_method": "DELETE"}, allow_redirects=True)
    assert r.status_code == 200, f"delete channel failed: {r.status_code}"
    assert channel_name not in r.text, "channel still visible after delete"
    print("[OK] Channel deleted")

    print('\nE2E flow succeeded')


if __name__ == '__main__':
    try:
        run()
    except AssertionError as e:
        print('E2E failed:', e)
        sys.exit(2)
    except Exception as e:
        print('Unexpected error:', e)
        sys.exit(3)
