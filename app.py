from flask import Flask
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get environment variables
polygon_rpc_url = os.getenv("POLYGON_RPC_URL")
contract_address = os.getenv("CONTRACT_ADDRESS")
account_private_key = os.getenv("ACCOUNT_PRIVATE_KEY")

app = Flask(__name__)

# Register your blueprints and configure the app

if __name__ == "__main__":
    app.run()
