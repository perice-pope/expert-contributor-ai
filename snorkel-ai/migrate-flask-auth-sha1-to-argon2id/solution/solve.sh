# CANARY_STRING_PLACEHOLDER

#!/bin/bash
set -euo pipefail

# Solution: Migrate Flask Auth Service from SHA-1 to Argon2id
# This script fixes the broken starter code to implement:
# 1. Argon2id password hashing in auth service
# 2. Automatic rehash-on-login when parameters are outdated
# 3. Bulk migration CLI with credential validation
# 4. Audit report generation

cd /app

# Fix auth_service.py to use Argon2id
cat > auth_service.py << 'AUTH_EOF'
#!/usr/bin/env python3
"""
Flask authentication service with Argon2id password hashing.
Supports backward compatibility with SHA-1 during migration.
"""

import hashlib
import json
import os
import re
from flask import Flask, request, jsonify
import argon2

app = Flask(__name__)

USERS_FILE = "/app/users.json"
CONFIG_FILE = "/app/argon2_config.json"

# Initialize Argon2 password hasher
_hasher = None


def get_hasher():
    """Get or create Argon2 password hasher with current config."""
    global _hasher
    if _hasher is None:
        config = load_config()
        _hasher = argon2.PasswordHasher(
            memory_cost=config['memory_cost'],
            time_cost=config['time_cost'],
            parallelism=config['parallelism']
        )
    return _hasher


def load_config():
    """Load Argon2 configuration from JSON file."""
    if not os.path.exists(CONFIG_FILE):
        return {"memory_cost": 65536, "time_cost": 3, "parallelism": 4}
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


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


def is_sha1_hash(hash_value):
    """Check if hash is legacy SHA-1 (40 hex chars, no prefix)."""
    return isinstance(hash_value, str) and len(hash_value) == 40 and \
           all(c in '0123456789abcdef' for c in hash_value.lower())


def is_argon2id_hash(hash_value):
    """Check if hash is Argon2id (starts with $argon2id$)."""
    return isinstance(hash_value, str) and hash_value.startswith('$argon2id$')


def get_hash_parameters(hash_value):
    """Extract memory_cost and time_cost from Argon2id hash string."""
    if not is_argon2id_hash(hash_value):
        return None
    
    # Argon2id hash format: $argon2id$v=<version>$m=<memory>,t=<time>,p=<parallelism>$<salt>$<hash>
    match = re.search(r'\$m=(\d+),t=(\d+),p=(\d+)\$', hash_value)
    if match:
        return {
            'memory_cost': int(match.group(1)),
            'time_cost': int(match.group(2)),
            'parallelism': int(match.group(3))
        }
    return None


def needs_rehash(stored_hash, current_config):
    """Check if stored hash needs rehashing due to outdated parameters."""
    if not is_argon2id_hash(stored_hash):
        return False  # SHA-1 hashes are handled separately
    
    stored_params = get_hash_parameters(stored_hash)
    if not stored_params:
        return False
    
    # Rehash if memory_cost or time_cost differ from current config
    return (stored_params['memory_cost'] != current_config['memory_cost'] or
            stored_params['time_cost'] != current_config['time_cost'])


def verify_password(password, stored_hash):
    """Verify password against stored hash (supports SHA-1 and Argon2id)."""
    if is_sha1_hash(stored_hash):
        return verify_sha1(password, stored_hash)
    elif is_argon2id_hash(stored_hash):
        try:
            hasher = get_hasher()
            hasher.verify(stored_hash, password)
            return True
        except (argon2.exceptions.VerifyMismatchError, argon2.exceptions.VerificationError):
            return False
    return False


def hash_password_argon2id(password):
    """Hash password with Argon2id using current config."""
    hasher = get_hasher()
    return hasher.hash(password)


@app.route('/login', methods=['POST'])
def login():
    """Handle login requests with automatic rehash-on-login."""
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
    
    # Verify password (supports both SHA-1 and Argon2id)
    if not verify_password(password, stored_hash):
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401
    
    # Check if rehashing is needed
    current_config = load_config()
    if needs_rehash(stored_hash, current_config):
        # Rehash with current parameters
        new_hash = hash_password_argon2id(password)
        user['password_hash'] = new_hash
        save_users(users)
    
    return jsonify({"status": "success"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
AUTH_EOF

# Fix migrate.py to implement bulk migration
cat > migrate.py << 'MIGRATE_EOF'
#!/usr/bin/env python3
"""
CLI tool to bulk-migrate users from SHA-1 to Argon2id password hashing.
Reads login attempts from CSV and validates credentials before migrating.
"""

import csv
import json
import os
import hashlib
import re
import argon2

USERS_FILE = "/app/users.json"
LOGIN_ATTEMPTS_FILE = "/app/login_attempts.csv"
CONFIG_FILE = "/app/argon2_config.json"
AUDIT_FILE = "/app/audit.json"


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


def load_config():
    """Load Argon2 configuration from JSON file."""
    if not os.path.exists(CONFIG_FILE):
        return {"memory_cost": 65536, "time_cost": 3, "parallelism": 4}
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def hash_sha1(password):
    """Legacy SHA-1 hashing (unsalted, insecure)."""
    return hashlib.sha1(password.encode('utf-8')).hexdigest()


def verify_sha1(password, hash_value):
    """Verify password against SHA-1 hash."""
    return hash_sha1(password) == hash_value


def is_sha1_hash(hash_value):
    """Check if hash is legacy SHA-1 (40 hex chars, no prefix)."""
    return isinstance(hash_value, str) and len(hash_value) == 40 and \
           all(c in '0123456789abcdef' for c in hash_value.lower())


def hash_password_argon2id(password, config):
    """Hash password with Argon2id using provided config."""
    hasher = argon2.PasswordHasher(
        memory_cost=config['memory_cost'],
        time_cost=config['time_cost'],
        parallelism=config['parallelism']
    )
    return hasher.hash(password)


def main():
    """Main migration function."""
    users = load_users()
    config = load_config()
    
    migrated_count = 0
    failed_users = []
    
    # Read login attempts from CSV
    if not os.path.exists(LOGIN_ATTEMPTS_FILE):
        print(f"Error: {LOGIN_ATTEMPTS_FILE} not found")
        return
    
    with open(LOGIN_ATTEMPTS_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            username = row.get('username', '').strip()
            password = row.get('password', '').strip()
            
            if not username or not password:
                continue
            
            if username not in users:
                failed_users.append(username)
                continue
            
            user = users[username]
            stored_hash = user.get('password_hash', '')
            
            # Only migrate SHA-1 hashes (skip if already Argon2id)
            if not is_sha1_hash(stored_hash):
                # Already migrated or not SHA-1, skip
                continue
            
            # Validate password against SHA-1 hash
            if verify_sha1(password, stored_hash):
                # Migrate to Argon2id
                new_hash = hash_password_argon2id(password, config)
                user['password_hash'] = new_hash
                migrated_count += 1
            else:
                # Password validation failed
                failed_users.append(username)
    
    # Save updated users
    save_users(users)
    
    # Generate audit report
    audit = {
        "migrated_count": migrated_count,
        "failed_count": len(failed_users),
        "failed_users": sorted(list(set(failed_users)))  # Remove duplicates and sort
    }
    
    with open(AUDIT_FILE, 'w') as f:
        json.dump(audit, f, indent=2)
    
    print(f"Migration complete: {migrated_count} migrated, {len(failed_users)} failed")


if __name__ == '__main__':
    main()
MIGRATE_EOF

# Make scripts executable
chmod +x auth_service.py migrate.py

echo "Solution applied: Auth service and migration tool updated"
