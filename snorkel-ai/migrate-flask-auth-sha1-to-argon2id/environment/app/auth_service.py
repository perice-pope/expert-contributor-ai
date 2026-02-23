#!/usr/bin/env python3
"""
Legacy Flask authentication service with SHA-1 password hashing.
Needs to be refactored to use Argon2id with per-user salts.
"""

import hashlib
import json
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

USERS_FILE = "/app/users.json"
CONFIG_FILE = "/app/argon2_config.json"


def load_users():
    """Load user database from JSON file."""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)


def save_users(users):
    """Save user database to JSON file."""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def hash_sha1(password):
    """Legacy SHA-1 hashing (unsalted, insecure)."""
    return hashlib.sha1(password.encode('utf-8')).hexdigest()


def verify_sha1(password, hash_value):
    """Verify password against SHA-1 hash."""
    return hash_sha1(password) == hash_value


@app.route('/login', methods=['POST'])
def login():
    """Handle login requests."""
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"status": "error", "message": "Missing username or password"}), 400
    
    username = data['username']
    password = data['password']
    
    users = load_users()
    
    if username not in users:
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401
    
    user = users[username]
    stored_hash = user.get('password_hash', '')
    
    # TODO: Implement Argon2id verification
    # TODO: Support backward compatibility with SHA-1 during migration
    # TODO: Implement automatic rehash-on-login when parameters are outdated
    
    # Current broken implementation: only checks SHA-1
    if verify_sha1(password, stored_hash):
        # TODO: Check if hash needs rehashing (compare parameters)
        # TODO: Rehash with Argon2id if needed
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)




