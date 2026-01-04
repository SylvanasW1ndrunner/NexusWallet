import requests


class PimlicoBundler:
    """Simple Pimlico bundler client for testing"""

    def __init__(self, api_key: str, chain_name: str):
        self.api_key = api_key
        self.chain_name = chain_name
        # Pimlico Sepolia endpoint
        self.bundler_url = f"https://public.pimlico.io/v2/11155111/rpc"

    def send_user_operation(self, user_op: dict, entry_point: str) -> str:
        """
        Send UserOperation to Pimlico bundler

        Args:
            user_op: UserOperation dict
            entry_point: EntryPoint address

        Returns:
            UserOperation hash
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_sendUserOperation",
            "params": [user_op, entry_point]
        }

        # Debug output
        print(f"\n[DEBUG] === Bundler Request Details ===")
        print(f"[DEBUG] URL: {self.bundler_url}")
        print(f"[DEBUG] Method: {payload['method']}")
        print(f"[DEBUG] EntryPoint: {entry_point}")
        print(f"[DEBUG] UserOp Keys: {list(user_op.keys())}")
        print(f"[DEBUG] UserOp.sender: {user_op.get('sender')}")
        print(f"[DEBUG] UserOp.nonce: {user_op.get('nonce')}")
        print(f"[DEBUG] UserOp.signature: {user_op.get('signature', 'N/A')[:66]}...")
        print(f"[DEBUG] Full payload (first 500 chars): {str(payload)}...")

        response = requests.post(self.bundler_url, json=payload)

        print(f"[DEBUG] Response Status: {response.status_code}")
        print(f"[DEBUG] Response Headers: {dict(response.headers)}")

        try:
            result = response.json()
            print(f"[DEBUG] Full Response: {result}")
        except Exception as e:
            print(f"[DEBUG] Failed to parse JSON: {e}")
            print(f"[DEBUG] Raw Response: {response.text}")
            raise

        if 'error' in result:
            error = result['error']
            print(f"\n[ERROR] === Bundler Error Details ===")
            print(f"[ERROR] Code: {error.get('code')}")
            print(f"[ERROR] Message: {error.get('message')}")
            if 'data' in error:
                print(f"[ERROR] Data: {error.get('data')}")
            raise Exception(f"Bundler error: {result['error']}")

        return result['result']

    def get_user_operation_receipt(self, user_op_hash: str) -> dict:
        """Get UserOperation receipt"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_getUserOperationReceipt",
            "params": [user_op_hash]
        }

        response = requests.post(self.bundler_url, json=payload)
        response.raise_for_status()

        result = response.json()
        return result.get('result')

    def get_UserOperation_GasPrice(self):
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "pimlico_getUserOperationGasPrice",
            "params": []
        }
        response = requests.post(self.bundler_url, json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get('result')