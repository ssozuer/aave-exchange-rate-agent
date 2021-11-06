# AAVE aToken(aUSDC/aDAI) Exchange Rate Agent

## Description

This agent detects if aToken1(aUSDC)/aToken2(aDAI) exchange rate drops.

## Supported Chains

- Ethereum

## Alerts

The following describes agent alert data.

- AAVE-3
  - Fired when exchange rate drops for given aToken assets
  - Severity is always set to "info" 
  - Type is always set to "info" 
  - Metadata information:
      "current_exchange_rate": current exchange rate 
      "previous_exchange_rate": previous exchange rate
      "aToken1": first asset symbol
      "aToken2": second asset symbol
      "aToken1_price": first asset price
      "aToken2_price": second asset price
