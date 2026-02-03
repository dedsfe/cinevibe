
import os
import sys

# Mock the environment variable
test_path = "/tmp/test_links.db"
os.environ["DB_FILE_PATH"] = test_path

try:
    from database import DB_PATH as DB_PATH_MAIN
    from database_series import DB_PATH as DB_PATH_SERIES
    
    print(f"Expected: {test_path}")
    print(f"Actual (database.py): {DB_PATH_MAIN}")
    print(f"Actual (database_series.py): {DB_PATH_SERIES}")
    
    if DB_PATH_MAIN == test_path and DB_PATH_SERIES == test_path:
        print("SUCCESS: Database paths are correctly configured from environment.")
    else:
        print("FAILURE: Database paths do not match environment variable.")
        sys.exit(1)
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)
        
