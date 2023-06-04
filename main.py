from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from services.blockchain import BlockchainService
from services.ocr import extract_id
import hashlib
from faker import Faker

fake = Faker()

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Get environment variables
polygon_rpc_url = os.getenv("POLYGON_RPC_URL")
contract_address = os.getenv("CONTRACT_ADDRESS")
account_private_key = os.getenv("ACCOUNT_PRIVATE_KEY")

# Initialize blockchain service
blockchain_service = BlockchainService(polygon_rpc_url, contract_address)


def recursive_dict(d):
    if isinstance(d, dict):
        return {k: recursive_dict(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [recursive_dict(v) for v in d]
    elif hasattr(d, "__dict__"):
        return recursive_dict(d.__dict__)
    else:
        return d


@app.route('/register', methods=['POST'])
def register():
    if 'id_image' not in request.files:
        return jsonify({'error': 'No ID image found in the request.'}), 400

    id_image = request.files['id_image']

    # Save the image to a temporary file
    temp_image_path = '/tmp/id_image.jpg'  # Provide a suitable temporary file path
    id_image.save(temp_image_path)

    # Extract the unique ID from the image
    unique_id = extract_id(temp_image_path)

    # Delete the temporary image file
    os.remove(temp_image_path)

    if not unique_id:
        return jsonify({'error': 'Failed to extract the unique ID from the image.'}), 400

    # Hash the unique ID here
    hashed_id = hashlib.sha256(unique_id.encode()).hexdigest()

    # Generate a random username
    username = fake.user_name()
    print(hashed_id, username)

    # Call the blockchain service to register the user
    registration_result = blockchain_service.register(hashed_id, username)

    if registration_result['status'] == 'failed':
        return jsonify({'error': 'Failed to register the user on the blockchain.'}), 500

    # Convert AttributeDict to dict to make it JSON serializable
    if 'txn_receipt' in registration_result:
        registration_result['txn_receipt'] = recursive_dict(
            registration_result['txn_receipt'])

    # Return a success response
    return jsonify({'status': 'success', 'txn_receipt': registration_result['txn_receipt'], 'username': username}), 200


@app.route('/vote', methods=['POST'])
def vote():
    if 'hashed_id' not in request.form or 'proposal_index' not in request.form or 'option_index' not in request.form:
        return jsonify({'error': 'Invalid vote data provided.'}), 400

    hashed_id = request.form['hashed_id']
    proposal_index = int(request.form['proposal_index'])
    option_index = int(request.form['option_index'])

    # Call the blockchain service to cast the vote
    vote_result = blockchain_service.vote(
        proposal_index, option_index, hashed_id)

    if vote_result['status'] == 'failed':
        return jsonify({'error': 'Failed to cast the vote on the blockchain.'}), 500

    # Convert AttributeDict to dict to make it JSON serializable
    if 'txn_receipt' in vote_result:
        vote_result['txn_receipt'] = recursive_dict(vote_result['txn_receipt'])

    # Return a success response
    return jsonify({'status': 'success', 'txn_receipt': vote_result['txn_receipt']}), 200


@app.route('/proposals', methods=['GET'])
def get_proposals():
    proposal_count = blockchain_service.contract.functions.getProposalCount().call()
    proposals = []
    for i in range(proposal_count):
        proposal_data = blockchain_service.contract.functions.proposals(
            i).call()
        options = []
        if len(proposal_data) >= 3:
            for option in proposal_data[2]:
                options.append(option)
        proposal = {
            'description': proposal_data[0],
            'deadline': proposal_data[1],
            'options': options
        }
        proposals.append(proposal)
    return jsonify({'proposals': proposals})


if __name__ == '__main__':
    app.run()
