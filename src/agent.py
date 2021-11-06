from eth_typing import abi
from forta_agent import Finding, FindingType, FindingSeverity, Web3, get_web3_provider
from .abis import *
from .utils import *

findings_count = 0
exchange_rate_data = None

def provide_handle_block(w3, data_provider, price_oracle):
    def handle_block(block_event):
        global exchange_rate_data
        global findings_count
        findings = []
        block_number = int(block_event.block_number)

        # limiting this agent to emit only 5 findings so that the alert feed is not spammed
        if findings_count >= 5:
            return findings
        
        assets = data_provider.functions.getAllATokens().call(block_identifier=block_number)
        asset1 = None
        asset2 = None

        for asset in assets:
            if ASSET1_SYMBOL == asset[0]:
                asset1 = asset
            if ASSET2_SYMBOL == asset[0]:
                asset2 = asset
            
            if asset1 and asset2:
                break
        
        # create asset contracts
        aToken1 = w3.eth.contract(address=Web3.toChecksumAddress(asset1[1]), abi=AAVE_V2_ATOKEN_ABI)
        aToken2 = w3.eth.contract(address=Web3.toChecksumAddress(asset2[1]), abi=AAVE_V2_ATOKEN_ABI)

        # get underlying token addresses
        aToken1_underlying = aToken1.functions.UNDERLYING_ASSET_ADDRESS().call(block_identifier=block_number)
        aToken2_underlying = aToken2.functions.UNDERLYING_ASSET_ADDRESS().call(block_identifier=block_number)

        # get underlying token pricess in eth
        prices = price_oracle.functions.getAssetsPrices([aToken1_underlying, aToken2_underlying]).call(block_identifier=block_number)

        if prices[0] == 0 or prices[1] == 0:
            return findings
        
        exchange_rate = prices[0] / prices[1]
        if exchange_rate_data is None:
            exchange_rate_data = exchange_rate
            return findings

        if exchange_rate_data > exchange_rate:
            findings.append(Finding({
                'name': 'AAVE aToken Exchange Rate Agent',
                'description': f'{asset1[0]} / {asset2[0]} exchange rate went down.',
                'alert_id': 'AAVE-3',
                'type': FindingType.Info,
                'severity': FindingSeverity.Info,
                'metadata': {
                    'current_exchange_rate': exchange_rate,
                    'previous_exchange_rate': exchange_rate_data,
                    'aToken1': asset1[0],
                    'aToken2': asset2[0],
                    'aToken1_price': prices[0],
                    'aToken2_price': prices[1]
                }
            }))
            findings_count += 1

        exchange_rate_data = exchange_rate
        return findings
    return handle_block

# create Aave data provider
w3 = get_web3_provider()
aave_data_provider = w3.eth.contract(address=Web3.toChecksumAddress(AAVE_V2_DATA_PROVIDER_ADDRESS), abi=AAVE_V2_DATA_PROVIDER_ABI)

# create Aave lending pool address provider
lendig_pool_addresses_provider_addr = aave_data_provider.functions.ADDRESSES_PROVIDER().call()
lending_pool_addresses_provider = w3.eth.contract(address=Web3.toChecksumAddress(lendig_pool_addresses_provider_addr), abi=AAVE_V2_LENDING_POOL_ADDRESSES_PROVIDER_ABI)

# get Aave lending pool address
lending_pool_addr = lending_pool_addresses_provider.functions.getLendingPool().call()

# create Aave price oracle
price_oracle_addr = lending_pool_addresses_provider.functions.getPriceOracle().call()
price_oracle = w3.eth.contract(address=Web3.toChecksumAddress(price_oracle_addr), abi=AAVE_V2_PRICE_ORACLE_ABI)

# init provider function
init_handle_block = provide_handle_block(w3, aave_data_provider, price_oracle)

# return handle block implementation
def handle_block(block_event):
    return  init_handle_block(block_event)

