diff --git a/base_token.sol b/base_token.sol
new file mode 100644
index 0000000..e1a2b34
--- /dev/null
+++ b/base_token.sol
@@
+// SPDX-License-Identifier: MIT
+pragma solidity ^0.8.20;
+
+/**
+ * @title BaseToken
+ * @dev Very small ERC‑20 implementation – enough for testing, demos, or as a
+ *      starting point for a custom token.  It follows the OpenZeppelin
+ *      interface but does not import any external libraries, keeping the
+ *      source single‑file.
+ */
+contract BaseToken {
+    // ------------------------------------------------------------------------
+    // Token metadata
+    // ------------------------------------------------------------------------
+    string public name;
+    string public symbol;
+    uint8 public immutable decimals = 18;
+
+    // ------------------------------------------------------------------------
+    // Balances & allowances
+    // ------------------------------------------------------------------------
+    uint256 public totalSupply;
+    mapping(address => uint256) public balanceOf;
+    mapping(address => mapping(address => uint256)) public allowance;
+
+    // ------------------------------------------------------------------------
+    // Events (standard ERC‑20)
+    // ------------------------------------------------------------------------
+    event Transfer(address indexed from, address indexed to, uint256 value);
+    event Approval(address indexed owner, address indexed spender, uint256 value);
+
+    // ------------------------------------------------------------------------
+    // Constructor
+    // ------------------------------------------------------------------------
+    constructor(string memory _name, string memory _symbol, uint256 _initialSupply) {
+        name = _name;
+        symbol = _symbol;
+        _mint(msg.sender, _initialSupply);
+    }
+
+    // ------------------------------------------------------------------------
+    // ERC‑20 core functions
+    // ------------------------------------------------------------------------
+    function transfer(address _to, uint256 _value) external returns (bool) {
+        _transfer(msg.sender, _to, _value);
+        return true;
+    }
+
+    function approve(address _spender, uint256 _value) external returns (bool) {
+        allowance[msg.sender][_spender] = _value;
+        emit Approval(msg.sender, _spender, _value);
+        return true;
+    }
+
+    function transferFrom(address _from, address _to, uint256 _value) external returns (bool) {
+        uint256 allowed = allowance[_from][msg.sender];
+        require(allowed >= _value, "ERC20: transfer amount exceeds allowance");
+        allowance[_from][msg.sender] = allowed - _value;
+        _transfer(_from, _to, _value);
+        return true;
+    }
+
+    // ------------------------------------------------------------------------
+    // Internal helpers
+    // ------------------------------------------------------------------------
+    function _transfer(address _from, address _to, uint256 _value) internal {
+        require(_to != address(0), "ERC20: transfer to the zero address");
+        uint256 fromBalance = balanceOf[_from];
+        require(fromBalance >= _value, "ERC20: transfer amount exceeds balance");
+        balanceOf[_from] = fromBalance - _value;
+        balanceOf[_to] += _value;
+        emit Transfer(_from, _to, _value);
+    }
+
+    function _mint(address _account, uint256 _value) internal {
+        require(_account != address(0), "ERC20: mint to the zero address");
+        totalSupply += _value;
+        balanceOf[_account] += _value;
+        emit Transfer(address(0), _account, _value);
+    }
+}
\ No newline at end of file
diff --git a/deploy_token.py b/deploy_token.py
new file mode 100644
index 0000000..d4f6a12
--- /dev/null
+++ b/deploy_token.py
@@
+#!/usr/bin/env python3
+"""
+Deploy the BaseToken contract using web3.py.
+
+Prerequisites
+-------------
+* Python 3.9+  
+* `pip install -r requirements.txt` (see below)  
+* An Ethereum JSON‑RPC endpoint (Infura, Alchemy, local node, etc.)  
+* The private key of the deployer account (keep it safe!)
+
+Usage
+-----
+```bash
+python deploy_token.py --rpc https://mainnet.infura.io/v3/$PROJECT_ID \\
+    --private-key 0xYOUR_PRIVATE_KEY \\
+    --name "MyBaseToken" \\
+    --symbol "MBT" \\
+    --supply 1000000
+```
+"""
+
+import argparse
+import json
+import os
+from pathlib import Path
+
+from web3 import Web3
+from solcx import compile_source, install_solc
+
+\n+def compile_contract(solidity_path: Path) -> dict:
+    \"\"\"Compile the Solidity contract and return the ABI + bytecode.\"\"\"
+    # Ensure a recent compiler version is available
+    install_solc("0.8.20")
+    with open(solidity_path, "r", encoding="utf-8") as file:
+        source = file.read()
+    compiled = compile_source(
+        source,
+        output_values=["abi", "bin"],
+        solc_version="0.8.20",
+    )
+    contract_id, contract_interface = compiled.popitem()
+    return contract_interface
+\n+def main() -> None:\n+    parser = argparse.ArgumentParser(description=\"Deploy BaseToken contract\")\n+    parser.add_argument(\"--rpc\", required=True, help=\"Ethereum JSON‑RPC endpoint URL\")\n+    parser.add_argument(\"--private-key\", required=True, help=\"Deployer private key\")\n+    parser.add_argument(\"--name\", required=True, help=\"Token name\")\n+    parser.add_argument(\"--symbol\", required=True, help=\"Token symbol\")\n+    parser.add_argument(\n+        \"--supply\",\n+        type=int,\n+        required=True,\n+        help=\"Initial supply (in whole tokens, will be multiplied by 10**decimals)\",\n+    )\n+    args = parser.parse_args()\n+\n+    w3 = Web3(Web3.HTTPProvider(args.rpc))\n+    if not w3.is_connected():\n+        raise RuntimeError(\"Unable to connect to the RPC endpoint\")\n+\n+    acct = w3.eth.account.from_key(args.private_key)\n+    w3.eth.default_account = acct.address\n+\n+    # Compile contract\n+    contract_path = Path(__file__).parent / \"base_token.sol\"\n+    iface = compile_contract(contract_path)\n+    abi = iface[\"abi\"]\n+    bytecode = iface[\"bin\"]\n+\n+    # Prepare constructor arguments\n+    initial_supply = args.supply * (10 ** 18)  # decimals = 18\n+    Token = w3.eth.contract(abi=abi, bytecode=bytecode)\n+    construct_txn = Token.constructor(args.name, args.symbol, initial_supply).build_transaction(\n+        {\n+            \"from\": acct.address,\n+            \"nonce\": w3.eth.get_transaction_count(acct.address),\n+            \"gas\": 2_000_000,\n+            \"gasPrice\": w3.to_wei(\"5\", \"gwei\"),\n+        }\n+    )\n+\n+    # Sign & send\n+    signed_txn = w3.eth.account.sign_transaction(construct_txn, private_key=args.private_key)\n+    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)\n+    print(f\"Deploy transaction sent – hash: {tx_hash.hex()}\")\n+    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)\n+    print(f\"Contract deployed at address: {receipt.contractAddress}\")\n+\n+\n+if __name__ == \"__main__\":\n+    main()\n+\n*** End of File ***
diff --git a/requirements.txt b/requirements.txt
new file mode 100644
index 0000000..4b1c7c2
--- /dev/null
+++ b/requirements.txt
@@
+web3>=6.0.0
+py-solc-x>=1.1.1
+
*** End of File ***
diff --git a/README.md b/README.md
new file mode 100644
index 0000000..c7a9f42
--- /dev/null
+++ b/README.md
@@
+# Base Token (Python + Solidity)
+
+This repository contains a **minimal ERC‑20 token** (`BaseToken`) written in Solidity and a **Python helper** that compiles and deploys the contract via `web3.py`.
+
+## Files
+
+| File                | Purpose                                                            |
+|---------------------|--------------------------------------------------------------------|
+| `base_token.sol`    | Simple ERC‑20 implementation (no external dependencies).          |
+| `deploy_token.py`   | Python script that compiles the contract and sends a deployment tx.|
+| `requirements.txt`  | Exact versions of the Python dependencies.                        |
+| `README.md`          | This documentation.                                               |
+
+## Getting started
+
+```bash
+# Clone the repo
+git clone https://github.com/your‑username/base-token.git
+cd base-token
+
+# Install dependencies (prefer a virtualenv)
+python -m venv .venv && source .venv/bin/activate
+pip install -r requirements.txt
+```
+
+### Deploying
+
+You need an Ethereum RPC endpoint and the private key of the account that will deploy the contract.
+
+```bash
+python deploy_token.py \\
+    --rpc https://goerli.infura.io/v3/YOUR_PROJECT_ID \\
+    --private-key 0xYOUR_PRIVATE_KEY \\
+    --name "MyBaseToken" \\
+    --symbol "MBT" \\
+    --supply 1_000_000
+```
+
+The script prints the transaction hash and the final contract address.
+
+## License
+
+MIT – feel free to fork, modify, and use it in your projects.
+
*** End of File ***
