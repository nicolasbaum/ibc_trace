import requests
import hashlib
from itertools import combinations


# Helper function to hash IBC paths
def hash_denom(path: str, base_denom: str) -> str:
    return hashlib.sha256((path + base_denom).encode('utf-8')).hexdigest().upper()


# Function to get token balances from a chain
def get_token_balances(chain_name: str, address: str) -> dict:
    endpoint = REST_ENDPOINTS.get(chain_name)
    if not endpoint:
        print(f"No RPC endpoint found for chain: {chain_name}")
        return {}

    url = f"{endpoint}/cosmos/bank/v1beta1/balances/{address}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Error fetching balances for chain: {chain_name}")
        return {}

    data = response.json()
    balances = {balance['denom']: int(balance['amount']) for balance in data.get('balances', [])}
    return balances


def build_path(channel: str) -> str:
    return f"transfer/{channel}/"


def build_denom(origin_chain: str, dest_chain: str, base_denom: str, current_path='') -> tuple[str, str]:
    channel = CHAIN_CHANNELS.get(origin_chain, {}).get(dest_chain)
    if not channel:
        return ""
    path = build_path(channel)
    new_path = path+current_path
    hashed_denom = hash_denom(new_path, base_denom)
    return f"ibc/{hashed_denom}", new_path


# Function to decode IBC path
def decode_ibc_path(ibc_denom: str, original_chain: str, base_denoms: dict, chain_channels: dict):
    MAX_ITERATIONS = 6
    if not ibc_denom.startswith("ibc/"):
        return [original_chain]

    iteration = 1
    possible_chains = chain_channels.keys()-{original_chain}
    for iteration in range(1, MAX_ITERATIONS):
        for base_denom in base_denoms.values():
            possibilities = combinations(possible_chains, iteration)
            for combination in possibilities:
                current_chain = original_chain
                path = ''
                for chain in combination:
                    denom, new_path = build_denom(current_chain, chain, base_denom, path)
                    current_chain = chain
                    path = new_path
                # print(f"{base_denom} - {combination}")
                if denom == ibc_denom:
                    return [original_chain] + list(combination)
    return []


# Main function to track tokens
def track_tokens(user_addresses: dict, original_denoms: dict, chain_channels: dict):
    total_dAsset = 0
    total_lAsset = 0

    results = {}

    for chain, address in user_addresses.items():
        balances = get_token_balances(chain, address)
        results[chain] = []

        for denom, amount in balances.items():
            if denom in original_denoms.values():
                results[chain].append((denom, denom, amount, [chain]))
                if denom == original_denoms['dAsset']:
                    total_dAsset += amount
                elif denom == original_denoms['lAsset']:
                    total_lAsset += amount
            elif denom.startswith('ibc/'):
                # Decode the IBC path and trace back the token
                path = decode_ibc_path(denom, "neutron-1", original_denoms, chain_channels)
                if path:
                    orig_denom = original_denoms['dAsset'] if 'dAsset' in denom else original_denoms['lAsset']
                    results[chain].append((denom, orig_denom, amount, path))

    print("TOTAL AMOUNTS:")
    print(f"{original_denoms['dAsset']}, {total_dAsset}")
    print(f"{original_denoms['lAsset']}, {total_lAsset}")

    return results


REST_ENDPOINTS = {
    "neutron-1": "https://neutron-rest.publicnode.com",
    "osmosis-1": "https://lcd.osmosis.zone",
    "phoenix-1": "https://phoenix-lcd.terra.dev",
    "stargaze-1": "https://api-stargaze.d-stake.xyz",
    "cosmoshub-4": "https://rest-cosmoshub.architectnodes.com",
    "stride-1": "https://rpc-stride-01.stakeflow.io"
}

USER_ADDRESSES = {
    "neutron-1": "neutron1lzecpea0qxw5xae92xkm3vaddeszr278k7w20c",
    "osmosis-1": "osmo1lzecpea0qxw5xae92xkm3vaddeszr278665crd",
    "phoenix-1": "terra1w7mtx2g478kkhs6pgynpcjpt6aw4930q34j36v",
    "stargaze-1": "stars1lzecpea0qxw5xae92xkm3vaddeszr278xas47w",
    "cosmoshub-4": "cosmos1lzecpea0qxw5xae92xkm3vaddeszr278jp8g4l",
    "stride-1": "stride1lzecpea0qxw5xae92xkm3vaddeszr2783285pn"
}

ORIGINAL_DENOMS = {
    "dAsset": "factory/neutron1lzecpea0qxw5xae92xkm3vaddeszr278k7w20c/dAsset",
    "lAsset": "factory/neutron1lzecpea0qxw5xae92xkm3vaddeszr278k7w20c/lAsset"
}

CHAIN_CHANNELS = {
    "neutron-1": {
        "osmosis-1": "channel-10",
        "phoenix-1": "channel-25",
        "stargaze-1": "channel-18",
        "cosmoshub-4": "channel-1",
        "stride-1": "channel-8"
    },
    "osmosis-1": {
        "neutron-1": "channel-874",
        "phoenix-1": "channel-251",
        "stargaze-1": "channel-75",
        "cosmoshub-4": "channel-0",
        "stride-1": "channel-326"
    },
    "phoenix-1": {
        "neutron-1": "channel-229",
        "osmosis-1": "channel-1",
        "stargaze-1": "channel-324",
        "cosmoshub-4": "channel-0",
        "stride-1": "channel-46"
    },
    "stargaze-1": {
        "neutron-1": "channel-191",
        "osmosis-1": "channel-0",
        "phoenix-1": "channel-266",
        "cosmoshub-4": "channel-239",
        "stride-1": "channel-106"
    },
    "cosmoshub-4": {
        "neutron-1": "channel-569",
        "osmosis-1": "channel-141",
        "phoenix-1": "channel-339",
        "stargaze-1": "channel-730",
        "stride-1": "channel-391"
    },
    "stride-1": {
        "neutron-1": "channel-123",
        "osmosis-1": "channel-5",
        "phoenix-1": "channel-52",
        "stargaze-1": "channel-19",
        "cosmoshub-4": "channel-0",
    }
}

if __name__ == '__main__':
    # Execute the function
    results = track_tokens(USER_ADDRESSES, ORIGINAL_DENOMS, CHAIN_CHANNELS)

    # Print results
    for chain, data in results.items():
        print(f"{chain}:")
        for entry in data:
            print(f"{entry[0]}, {entry[1]}, {entry[2]}, {entry[3]}")
