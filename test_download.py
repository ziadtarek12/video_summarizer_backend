#!/usr/bin/env python3
"""
Test script - EXACT copy of user's working code.
Run: python3 test_download.py
"""

import requests
import yt_dlp
import os

# 1. Configuration
# Replace with your actual Deployed Web App URL from Google Apps Script
GAS_URL = "https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec"
VIDEO_ID = "-2I7ZtfJslk"  # The video that was failing

def run_test_download(vid_id):
    print(f"[*] Step 1: Querying Google Apps Script Bridge for ID: {vid_id}...")
    
    try:
        # Call your Apps Script to get the validated title/status
        response = requests.get(f"{GAS_URL}?id={vid_id}", timeout=10)
        data = response.json()
        
        if data.get("status") != "success":
            print(f"[!] Bridge Error: {data.get('message', 'Unknown error')}")
            return

        video_title = data.get("title")
        print(f"[+] Bridge Success! Video Found: {video_title}")

        # 2. Configure yt-dlp
        # 'bestvideo+bestaudio/best' merges them into one high-quality file (usually .mkv or .mp4)
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best', 
            'outtmpl': f'%(title)s.%(ext)s', # Saves file as 'Title.ext'
            'noplaylist': True,
            'quiet': False, # Set to False to see the download progress
        }

        print(f"[*] Step 2: Starting download via yt-dlp...")
        
        video_url = f"https://www.youtube.com/watch?v={vid_id}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            
        print(f"\n[SUCCESS] Video '{video_title}' has been downloaded to your current folder.")

    except Exception as e:
        print(f"[!] An error occurred: {e}")

if __name__ == "__main__":
    run_test_download(VIDEO_ID)
