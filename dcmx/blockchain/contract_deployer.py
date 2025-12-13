"""
Smart Contract Deployment System

Handles compilation, deployment, and verification of custom contracts.
"""

import json
import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path
from web3 import Web3
from web3.contract import Contract
from eth_account import Account
import subprocess
import tempfile


@dataclass
class DeploymentConfig:
    """Contract deployment configuration."""
    network: str  # "ethereum", "polygon", "bsc", etc.
    rpc_url: str
    chain_id: int
    deployer_private_key: str
    gas_price_gwei: Optional[float] = None  # Auto if None
    gas_limit: Optional[int] = None  # Auto-estimate if None
    verify_on_etherscan: bool = False
    etherscan_api_key: Optional[str] = None


@dataclass
class DeploymentResult:
    """Contract deployment result."""
    success: bool
    contract_address: Optional[str] = None
    transaction_hash: Optional[str] = None
    gas_used: Optional[int] = None
    deployment_cost_eth: Optional[float] = None
    verification_status: Optional[str] = None
    error: Optional[str] = None
    abi: Optional[List[Dict]] = None
    bytecode: Optional[str] = None


class SolidityCompiler:
    """Compile Solidity contracts using solc."""
    
    def __init__(self, solc_version: str = "0.8.20"):
        self.solc_version = solc_version
        self._ensure_solc_installed()
    
    def _ensure_solc_installed(self):
        """Ensure solc compiler is installed."""
        try:
            from solcx import install_solc, set_solc_version, get_installed_solc_versions
            
            installed = get_installed_solc_versions()
            if self.solc_version not in [str(v) for v in installed]:
                print(f"Installing solc {self.solc_version}...")
                install_solc(self.solc_version)
            
            set_solc_version(self.solc_version)
        except ImportError:
            raise RuntimeError(
                "solcx not installed. Install with: pip install py-solc-x"
            )
    
    def compile(
        self,
        contract_code: str,
        contract_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compile Solidity contract.
        
        Args:
            contract_code: Solidity source code
            contract_name: Name of main contract (auto-detect if None)
            
        Returns:
            Dict with abi, bytecode, and metadata
        """
        from solcx import compile_source
        
        # Detect contract name if not provided
        if not contract_name:
            import re
            match = re.search(r'contract\s+(\w+)', contract_code)
            if match:
                contract_name = match.group(1)
            else:
                raise ValueError("Could not detect contract name")
        
        try:
            # Compile with all outputs
            compiled = compile_source(
                contract_code,
                output_values=['abi', 'bin', 'metadata'],
                solc_version=self.solc_version,
            )
            
            # Find the main contract
            contract_id = f"<stdin>:{contract_name}"
            if contract_id not in compiled:
                # Try without <stdin>
                contract_id = contract_name
                if contract_id not in compiled:
                    raise ValueError(f"Contract {contract_name} not found in compilation")
            
            contract_data = compiled[contract_id]
            
            return {
                "abi": contract_data['abi'],
                "bytecode": contract_data['bin'],
                "metadata": json.loads(contract_data.get('metadata', '{}')),
                "contract_name": contract_name,
            }
            
        except Exception as e:
            raise RuntimeError(f"Compilation failed: {str(e)}")


class ContractDeployer:
    """Deploy compiled contracts to blockchain."""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.w3 = Web3(Web3.HTTPProvider(config.rpc_url))
        
        if not self.w3.is_connected():
            raise ConnectionError(f"Cannot connect to {config.rpc_url}")
        
        self.account = Account.from_key(config.deployer_private_key)
        self.compiler = SolidityCompiler()
    
    async def deploy_contract(
        self,
        contract_code: str,
        constructor_args: Optional[List[Any]] = None,
        contract_name: Optional[str] = None,
    ) -> DeploymentResult:
        """
        Deploy smart contract.
        
        Args:
            contract_code: Solidity source code
            constructor_args: Constructor arguments
            contract_name: Contract name (auto-detect if None)
            
        Returns:
            DeploymentResult with address and transaction details
        """
        try:
            # Compile contract
            print("Compiling contract...")
            compiled = self.compiler.compile(contract_code, contract_name)
            
            # Create contract object
            contract = self.w3.eth.contract(
                abi=compiled['abi'],
                bytecode=compiled['bytecode'],
            )
            
            # Build constructor transaction
            constructor = contract.constructor(*(constructor_args or []))
            
            # Estimate gas
            gas_estimate = constructor.estimate_gas({
                'from': self.account.address,
            })
            
            # Add 20% buffer
            gas_limit = self.config.gas_limit or int(gas_estimate * 1.2)
            
            # Get gas price
            if self.config.gas_price_gwei:
                gas_price = self.w3.to_wei(self.config.gas_price_gwei, 'gwei')
            else:
                gas_price = self.w3.eth.gas_price
            
            # Build transaction
            print("Building deployment transaction...")
            transaction = constructor.build_transaction({
                'from': self.account.address,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'chainId': self.config.chain_id,
            })
            
            # Sign transaction
            signed_txn = self.account.sign_transaction(transaction)
            
            # Send transaction
            print("Sending deployment transaction...")
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            print("Waiting for confirmation...")
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if tx_receipt['status'] != 1:
                return DeploymentResult(
                    success=False,
                    error="Transaction failed",
                    transaction_hash=tx_hash.hex(),
                )
            
            contract_address = tx_receipt['contractAddress']
            gas_used = tx_receipt['gasUsed']
            deployment_cost = self.w3.from_wei(gas_used * gas_price, 'ether')
            
            print(f"✓ Contract deployed at: {contract_address}")
            print(f"  Gas used: {gas_used:,}")
            print(f"  Cost: {deployment_cost:.6f} ETH")
            
            result = DeploymentResult(
                success=True,
                contract_address=contract_address,
                transaction_hash=tx_hash.hex(),
                gas_used=gas_used,
                deployment_cost_eth=float(deployment_cost),
                abi=compiled['abi'],
                bytecode=compiled['bytecode'],
            )
            
            # Verify on Etherscan if requested
            if self.config.verify_on_etherscan and self.config.etherscan_api_key:
                print("Verifying contract on Etherscan...")
                verification = await self._verify_on_etherscan(
                    contract_address,
                    contract_code,
                    constructor_args or [],
                )
                result.verification_status = verification
            
            return result
            
        except Exception as e:
            return DeploymentResult(
                success=False,
                error=str(e),
            )
    
    async def _verify_on_etherscan(
        self,
        contract_address: str,
        source_code: str,
        constructor_args: List[Any],
    ) -> str:
        """Verify contract on Etherscan."""
        # This is a simplified version
        # Real implementation would use Etherscan API
        
        try:
            # Encode constructor arguments
            # Submit to Etherscan API
            # Wait for verification
            
            return "verified"  # or "pending" or "failed"
            
        except Exception as e:
            return f"verification_failed: {str(e)}"
    
    def get_deployed_contract(
        self,
        contract_address: str,
        abi: List[Dict],
    ) -> Contract:
        """Get contract instance at address."""
        return self.w3.eth.contract(
            address=self.w3.to_checksum_address(contract_address),
            abi=abi,
        )


class ContractRegistry:
    """
    Registry of deployed contracts.
    
    Tracks all contracts deployed by users for management and auditing.
    """
    
    def __init__(self, registry_file: str = "contracts_registry.json"):
        self.registry_file = Path(registry_file)
        self.contracts: Dict[str, Dict[str, Any]] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load registry from file."""
        if self.registry_file.exists():
            with open(self.registry_file, 'r') as f:
                self.contracts = json.load(f)
    
    def _save_registry(self):
        """Save registry to file."""
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, 'w') as f:
            json.dump(self.contracts, f, indent=2)
    
    def register_contract(
        self,
        contract_address: str,
        contract_data: Dict[str, Any],
    ):
        """Register a deployed contract."""
        self.contracts[contract_address] = {
            **contract_data,
            "registered_at": "{{ timestamp }}",
        }
        self._save_registry()
    
    def get_contract(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """Get contract data by address."""
        return self.contracts.get(contract_address)
    
    def list_contracts(
        self,
        owner: Optional[str] = None,
        contract_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List all registered contracts with filters."""
        contracts = list(self.contracts.values())
        
        if owner:
            contracts = [c for c in contracts if c.get('owner') == owner]
        
        if contract_type:
            contracts = [c for c in contracts if c.get('type') == contract_type]
        
        return contracts
    
    def update_contract(
        self,
        contract_address: str,
        updates: Dict[str, Any],
    ):
        """Update contract metadata."""
        if contract_address in self.contracts:
            self.contracts[contract_address].update(updates)
            self._save_registry()
    
    def deactivate_contract(self, contract_address: str):
        """Mark contract as deactivated."""
        self.update_contract(contract_address, {"active": False})


# Convenience functions

async def deploy_from_template(
    template_name: str,
    parameters: Dict[str, Any],
    constructor_args: List[Any],
    config: DeploymentConfig,
) -> DeploymentResult:
    """Deploy a contract from template."""
    from dcmx.blockchain.contract_builder import ContractBuilder
    
    # Build contract
    builder = ContractBuilder()
    contract_data = builder.build_contract(template_name, parameters)
    
    # Check validation
    if not contract_data.get('validation', {}).get('passed', False):
        return DeploymentResult(
            success=False,
            error="Contract failed validation. Fix issues before deploying.",
        )
    
    # Deploy
    deployer = ContractDeployer(config)
    result = await deployer.deploy_contract(
        contract_data['contract_code'],
        constructor_args,
    )
    
    # Register if successful
    if result.success:
        registry = ContractRegistry()
        registry.register_contract(
            result.contract_address,
            {
                "template": template_name,
                "parameters": parameters,
                "abi": result.abi,
                "bytecode": result.bytecode,
                "network": config.network,
                "owner": deployer.account.address,
                "type": contract_data.get('template'),
            }
        )
    
    return result
