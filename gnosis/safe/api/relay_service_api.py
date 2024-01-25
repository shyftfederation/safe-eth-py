from typing import TypedDict
from urllib.parse import urljoin

import requests
from eth_typing import ChecksumAddress, HexStr

from .. import SafeTx
from ..signatures import signature_split
from .base_api import SafeAPIException, SafeBaseAPI


class RelayEstimation(TypedDict):
    safeTxGas: int
    baseGas: int
    gasPrice: int
    lastUsedNonce: int
    gasToken: ChecksumAddress
    refundReceiver: ChecksumAddress


class RelaySentTransaction(TypedDict):
    safeTxHash: HexStr
    txHash: HexStr


class RelayServiceApi(SafeBaseAPI):
    URL_BY_NETWORK = {
        # Currently there's no official relayer operated
    }

    def send_transaction(
        self, safe_address: str, safe_tx: SafeTx
    ) -> RelaySentTransaction:
        url = urljoin(self.base_url, f"/api/v1/safes/{safe_address}/transactions/")
        signatures = []
        for i in range(len(safe_tx.signatures) // 65):
            v, r, s = signature_split(safe_tx.signatures, i)
            signatures.append(
                {
                    "v": v,
                    "r": r,
                    "s": s,
                }
            )

        data = {
            "to": safe_tx.to,
            "value": safe_tx.value,
            "data": safe_tx.data.hex() if safe_tx.data else None,
            "operation": safe_tx.operation,
            "gasToken": safe_tx.gas_token,
            "safeTxGas": safe_tx.safe_tx_gas,
            "dataGas": safe_tx.base_gas,
            "gasPrice": safe_tx.gas_price,
            "refundReceiver": safe_tx.refund_receiver,
            "nonce": safe_tx.safe_nonce,
            "signatures": signatures,
        }
        response = requests.post(url, json=data, timeout=self.request_timeout)
        if not response.ok:
            raise SafeAPIException(f"Error posting transaction: {response.content}")
        else:
            return RelaySentTransaction(response.json())

    def get_estimation(self, safe_address: str, safe_tx: SafeTx) -> RelayEstimation:
        """
        :param safe_address:
        :param safe_tx:
        :return: RelayEstimation
        """
        url = urljoin(
            self.base_url, f"/api/v2/safes/{safe_address}/transactions/estimate/"
        )
        data = {
            "to": safe_tx.to,
            "value": safe_tx.value,
            "data": safe_tx.data.hex() if safe_tx.data else None,
            "operation": safe_tx.operation,
            "gasToken": safe_tx.gas_token,
        }
        response = requests.post(url, json=data, timeout=self.request_timeout)
        if not response.ok:
            raise SafeAPIException(f"Error posting transaction: {response.content}")
        else:
            response_json = response.json()
            # Convert values to int
            for key in ("safeTxGas", "baseGas", "gasPrice"):
                response_json[key] = int(response_json[key])
            return RelayEstimation(response_json)
