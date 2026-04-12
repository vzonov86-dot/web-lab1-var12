import requests
import time
import sys

def test_homepage():
    try:
        r = requests.get('http://localhost:5000/')
        if r.status_code != 200:
            print("Homepage returned", r.status_code)
            return False
        print("Homepage OK")
        return True
    except Exception as e:
        print("Error:", e)
        return False

if __name__ == '__main__':
    time.sleep(2)
    success = test_homepage()
    sys.exit(0 if success else 1)
