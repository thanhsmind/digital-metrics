try:
    print("Importing app.models...")
    import app.models

    print("Successfully imported app.models")
except Exception as e:
    print(f"Error importing app.models: {str(e)}")

try:
    print("Importing app.api.v1.api...")
    import app.api.v1.api

    print("Successfully imported app.api.v1.api")
except Exception as e:
    print(f"Error importing app.api.v1.api: {str(e)}")

try:
    print("Importing app.main...")
    import app.main

    print("Successfully imported app.main")
except Exception as e:
    print(f"Error importing app.main: {str(e)}")

print("Debug complete!")
