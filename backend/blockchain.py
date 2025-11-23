"""Lightweight, version-compatible Web3 helpers for the backend.

This module tries to connect to a local Ganache node and provides
`add_log_to_chain(entry)` which will store a hash + risk code on-chain.

The implementation is intentionally small and defensive: it performs lazy
imports of `web3`, supports a few different web3.py API names, and falls
back to ABI-encoding if helper methods are missing.
"""
import json
from pathlib import Path
from typing import Optional, Tuple

from . import config

# Module-level handles (initialized lazily)
w3 = None
contract = None


def _find_address_in_truffle_artifact(data: dict) -> Optional[str]:
    nets = data.get('networks') or {}
    if not nets:
        return None
    try:
        ids = sorted(int(k) for k in nets.keys())
        for nid in reversed(ids):
            entry = nets.get(str(nid)) or nets.get(nid)
            if isinstance(entry, dict) and entry.get('address'):
                return entry['address']
    except Exception:
        for v in nets.values():
            if isinstance(v, dict) and v.get('address'):
                return v['address']
    return None


def _to_checksum(w3_client, addr: str) -> str:
    try:
        from eth_utils import to_checksum_address
        return to_checksum_address(addr)
    except Exception:
        pass
    try:
        if hasattr(w3_client, 'toChecksumAddress'):
            return w3_client.toChecksumAddress(addr)
        if hasattr(w3_client, 'to_checksum_address'):
            return w3_client.to_checksum_address(addr)
    except Exception:
        pass
    try:
        from web3 import Web3 as _Web3
        if hasattr(_Web3, 'to_checksum_address'):
            return _Web3.to_checksum_address(addr)
    except Exception:
        pass
    return addr


def _to_wei(w3_client, val, unit='gwei') -> int:
    try:
        if hasattr(w3_client, 'toWei'):
            return w3_client.toWei(val, unit)
        else:
            from web3 import Web3 as _Web3
            return _Web3.to_wei(val, unit)
    except Exception:
        if unit == 'gwei':
            return int(float(val) * 10**9)
        return int(val)


def _is_connected(w3_client) -> bool:
    try:
        if hasattr(w3_client, 'is_connected'):
            return w3_client.is_connected()
        if hasattr(w3_client, 'isConnected'):
            return w3_client.isConnected()
    except Exception:
        return False
    return False


def load_contract() -> Tuple[Optional[object], Optional[object]]:
    """Attempt to load web3 and the contract (best-effort).

    Reads `config.CONTRACT_DATA_FILE` which can be either a Truffle artifact
    (with `abi` and `networks`) or a simple JSON with `abi` and `address`.
    """
    global w3, contract

    if w3 is not None and contract is not None:
        return w3, contract

    if not (config.GANACHE_URL and config.CHAIN_PRIVATE_KEY and config.CHAIN_ACCOUNT_ADDRESS and config.CONTRACT_DATA_FILE):
        print("[blockchain] Missing configuration (GANACHE_URL / CHAIN_*) — blockchain disabled")
        return None, None

    try:
        # Lazy import
        from web3 import Web3
        # Defensive PoA middleware import
        try:
            from web3.middleware.geth_poa import geth_poa_middleware as _poa
        except Exception:
            try:
                from web3.middleware import geth_poa_middleware as _poa
            except Exception:
                _poa = None

        path = Path(config.CONTRACT_DATA_FILE)
        if not path.exists():
            print(f"[blockchain] Artifact not found: {path}")
            return None, None

        raw = json.loads(path.read_text(encoding='utf-8'))
        abi = raw.get('abi')
        address = raw.get('address') or _find_address_in_truffle_artifact(raw)
        if not abi or not address:
            print("[blockchain] ABI or address missing in artifact")
            return None, None

        w3 = Web3(Web3.HTTPProvider(config.GANACHE_URL))
        if _poa:
            try:
                w3.middleware_onion.inject(_poa, layer=0)
            except Exception:
                pass

        if not _is_connected(w3):
            print(f"[blockchain] Cannot connect to Ganache at {config.GANACHE_URL}")
            return None, None

        contract = w3.eth.contract(address=_to_checksum(w3, address), abi=abi)
        print(f"[blockchain] Connected to chain. Contract at {address}")
        return w3, contract

    except Exception as e:
        print(f"[blockchain] Error initializing web3/contract: {e}")
        return None, None


# initialize on import (best-effort)
w3, contract = load_contract()


def add_log_to_chain(entry: dict) -> bool:
    """Hash a log and store it on-chain. Returns True on success."""
    global w3, contract

    if w3 is None or contract is None:
        w3, contract = load_contract()
        if w3 is None or contract is None:
            print("[blockchain] web3 non disponible; fonctionnalités désactivées")
            return False
    try:
        log_string = (
            f"(STATUS={entry.get('status','False')}"
            f" USERID={entry.get('userid','Unknown')}"
            f" IP={entry.get('ip','Unknown')}"
            f" COUNTRY={entry.get('country','Unknown')}"
            f" DEVICE={entry.get('device','Unknown')}"
            f" BROWSER={entry.get('browser','Unknown')})"
        )

        log_hash = w3.keccak(text=log_string)
        risk_code = entry.get('risk', 'benin')

        try:
            from eth_utils import to_checksum_address
            account = to_checksum_address(config.CHAIN_ACCOUNT_ADDRESS)
        except Exception:
            account = _to_checksum(w3, config.CHAIN_ACCOUNT_ADDRESS)

        nonce = w3.eth.get_transaction_count(account)

        func = contract.functions.recordLog(log_hash, risk_code)

        tx_dict = {'from': account, 'nonce': nonce, 'gas': 300000, 'gasPrice': _to_wei(w3, '20', 'gwei')}

        # try common helper names, then fallback to ABI encode
        tx = None
        try:
            tx = func.buildTransaction(tx_dict)
        except Exception:
            try:
                tx = func.build_transaction(tx_dict)
            except Exception:
                try:
                    data = contract.encodeABI(fn_name='recordLog', args=[log_hash, risk_code])
                except Exception:
                    data = contract.encodeABI('recordLog', [log_hash, risk_code])
                tx = {**tx_dict, 'to': getattr(contract, 'address', getattr(contract, '_address', None)), 'data': data}

        signed = w3.eth.account.sign_transaction(tx, private_key=config.CHAIN_PRIVATE_KEY)
        raw = getattr(signed, 'raw_transaction', None) or getattr(signed, 'rawTransaction', None)
        tx_hash = w3.eth.send_raw_transaction(raw)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        # normalize receipt status
        status = None
        try:
            status = receipt.get('status', None)
        except Exception:
            try:
                status = getattr(receipt, 'status', None)
            except Exception:
                status = None

        success = status == 1 or status is True
        try:
            hex_hash = tx_hash.hex()
        except Exception:
            hex_hash = str(tx_hash)
        print(f"[blockchain] tx {hex_hash} pour {risk_code} - Status: {success}")
        return success
    except Exception as e:
        print(f"[blockchain] Erreur d'envoi de la transaction: {e}")
        return False